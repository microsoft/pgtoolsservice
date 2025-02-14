# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from logging import Logger

from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.kernel import Kernel

from ossdbtoolsservice.chat.completion.vscode_chat_prompt_execution_settings import (
    VSCodeChatPromptExecutionSettings,
)
from ossdbtoolsservice.chat.messages import (
    CHAT_COMPLETION_RESULT_METHOD,
    CHAT_REQUEST,
    ChatCompletionRequestParams,
    ChatCompletionResult,
)
from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.hosting import Service, ServiceProvider
from ossdbtoolsservice.hosting.context import NotificationContext, RequestContext
from ossdbtoolsservice.hosting.message_server import MessageServer
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.utils.async_runner import AsyncRunner

from .completion.completion_response_queues import CompletionResponseQueues
from .completion.messages import (
    VSCODE_LM_COMPLETION_RESPONSE,
    VSCodeLanguageModelChatCompletionResponse,
)
from .completion.vscode_chat_completion import VSCodeChatCompletion
from .plugin.postgres_plugin import PostgresPlugin
from .prompts import system_message_prompt


class ChatService(Service):
    def __init__(self) -> None:
        self._service_provider: ServiceProvider | None = None
        self._server: MessageServer | None = None
        self._logger: Logger | None = None

        # Mapping of completion request IDs to Queues
        self.completion_response_queues = CompletionResponseQueues()

        # Allow Azure OpenAI to be used with environment variables
        # TODO: Make this part of initialization logic during init call,
        #  allow services to fail gracefully.
        self._use_azure_openai = False
        if os.environ.get("PGTS_CHAT_USE_AZURE_OPENAI"):
            self._use_azure_openai = True
            # TODO: Validate environment variables

        self.executor = ThreadPoolExecutor(max_workers=10)

    def get_async_runner(self) -> AsyncRunner:
        if self._service_provider is None:
            raise ValueError("Service provider is not set")
        if self._service_provider.server.async_runner is None:
            raise ValueError("Async runner is required.")
        return self._service_provider.server.async_runner

    def register(self, service_provider: ServiceProvider) -> None:
        self._service_provider = service_provider
        self._server = service_provider.server
        self._logger = service_provider.logger

        # Register the request handlers
        self._service_provider.server.set_request_handler(
            CHAT_REQUEST, self._handle_chat_request
        )

        # Register notification handlers
        self._service_provider.server.set_notification_handler(
            VSCODE_LM_COMPLETION_RESPONSE, self._handle_completion_response
        )

        if self._service_provider.logger is not None:
            self._service_provider.logger.info("Chat service successfully initialized")

    def _handle_completion_response(
        self,
        _: NotificationContext,
        params: VSCodeLanguageModelChatCompletionResponse,
    ) -> None:
        self.get_async_runner().run(
            self.completion_response_queues.handle_completion_response(params)
        )

    def _handle_chat_request(
        self, request_context: RequestContext, params: ChatCompletionRequestParams
    ) -> None:
        def thread_target(
            request_context: RequestContext, params: ChatCompletionRequestParams
        ) -> None:
            try:
                self._process_chat_request(request_context, params)
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Error in chat request thread: {e}")
                request_context.send_error(str(e))

        self.executor.submit(thread_target, request_context, params)

    def _process_chat_request(
        self, request_context: RequestContext, params: ChatCompletionRequestParams
    ) -> None:
        if self._service_provider is None:
            raise ValueError("Service provider is not set")

        chat_id = str(uuid.uuid4())
        if self._logger:
            self._logger.info(f"Chat request received with id: {chat_id}")

        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("owner_uri is required")
            return

        doc_text = params.document

        kernel = Kernel()

        if self._use_azure_openai:
            chat_completion = AzureChatCompletion()
            execution_settings = AzureChatPromptExecutionSettings(
                function_choice_behavior=FunctionChoiceBehavior.Auto(),
                max_tokens=7000,
                temperature=0.7,
                top_p=0.8,
            )
        else:
            chat_completion = VSCodeChatCompletion(
                chat_id,
                request_context.send_notification,
                self.completion_response_queues,
                logger=self._logger,
            )
            # In VSCode, temperature, top_p etc are set in the extension
            execution_settings = VSCodeChatPromptExecutionSettings(
                function_choice_behavior=FunctionChoiceBehavior.Auto(),
            )

        kernel.add_service(chat_completion)

        connection_service = self._service_provider[constants.CONNECTION_SERVICE_NAME]
        if not isinstance(connection_service, ConnectionService):
            raise RuntimeError("Connection service is not set")

        postgres_plugin = PostgresPlugin(
            connection_service, request_context, chat_id, owner_uri, self._logger
        )
        postgres_plugin.add_to(kernel)

        history = ChatHistory()

        # Fetch schemas and tables to be injected into the system message
        db_context = postgres_plugin.get_db_context()
        system_message = system_message_prompt(doc_text=doc_text, db_context=db_context)

        history.add_system_message(system_message)

        for message in params.history or []:
            if message.participant == "user":
                history.add_user_message(message.content)
            else:
                history.add_assistant_message(message.content)

        # Add prompt as last user input
        if params.prompt:
            history.add_user_message(params.prompt)

        request_context.send_response(chat_id)

        async def process_response_stream() -> None:
            try:
                async for item in chat_completion.get_streaming_chat_message_contents(
                    history, execution_settings, kernel=kernel
                ):
                    for message in item:
                        if message.finish_reason == "stop":
                            request_context.send_notification(
                                CHAT_COMPLETION_RESULT_METHOD,
                                ChatCompletionResult.complete(
                                    chat_id,
                                    message.finish_reason,
                                ),
                            )
                        else:
                            content = "".join(
                                item.text or ""
                                for item in message.items
                                if isinstance(item, TextContent)
                            )
                            if content:
                                request_context.send_notification(
                                    CHAT_COMPLETION_RESULT_METHOD,
                                    ChatCompletionResult.response_part(
                                        chat_id=chat_id,
                                        role=message.role,
                                        content=content,
                                    ),
                                )
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Error processing completion: {e}")
                request_context.send_error(str(e))
                request_context.send_notification(
                    CHAT_COMPLETION_RESULT_METHOD,
                    ChatCompletionResult.error(chat_id, str(e)),
                )
                raise

        self.get_async_runner().run(process_response_stream())
