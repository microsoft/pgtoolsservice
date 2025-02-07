# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
from logging import Logger
import uuid
from concurrent.futures import ThreadPoolExecutor

from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
)
from semantic_kernel.contents import ChatHistory
from semantic_kernel.kernel import Kernel
from semantic_kernel.contents.text_content import TextContent

from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.chat.messages import (
    CHAT_REQUEST,
    CHAT_COMPLETION_RESULT_METHOD,
    ChatCompletionRequestParams,
    ChatCompletionResult,
)
from ossdbtoolsservice.hosting import (
    ServiceProvider,
)

from ossdbtoolsservice.hosting.context import NotificationContext, RequestContext
from ossdbtoolsservice.hosting.message_server import MessageServer

from .plugin.postgres_plugin import PostgresPlugin
from .prompts import system_message_prompt
from .completion.messages import (
    VSCODE_LM_COMPLETION_RESPONSE,
    VSCodeLanguageModelChatCompletionResponse,
)
from .completion.completion_response_queues import CompletionResponseQueues
from .completion.vscode_chat_completion import VSCodeChatCompletion


class ChatService(object):
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

        self.executor = ThreadPoolExecutor(
            max_workers=10
        )  # Adjust the number of workers as needed

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
        if self._service_provider is None:
            raise ValueError("Service provider is not set")
        if self._service_provider.async_runner is None:
            raise ValueError("Async runner is required.")

        self._service_provider.async_runner.run(
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
        if self._service_provider.async_runner is None:
            raise ValueError("Async runner is required.")

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
        else:
            chat_completion = VSCodeChatCompletion(
                chat_id,
                request_context.send_notification,
                self.completion_response_queues,
                logger=self._logger,
            )

        kernel.add_service(chat_completion)

        connection_service = self._service_provider[constants.CONNECTION_SERVICE_NAME]
        postgres_plugin = PostgresPlugin(
            connection_service, request_context, chat_id, owner_uri, self._logger
        )
        postgres_plugin.add_to(kernel)

        # we set the function choice to Auto, so that the LLM can choose the correct function to call.
        # and we exclude the ChatBot plugin, so that it does not call itself.
        # this means that it has access to 2 functions, that were defined above.
        execution_settings = AzureChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
            max_tokens=7000,
            temperature=0.7,
            top_p=0.8,
        )

        history = ChatHistory()

        # Fetch schemas and tables to be injected into the system message
        db_context = postgres_plugin.get_db_context()
        # db_context = None
        system_message = system_message_prompt(doc_text=doc_text, db_context=db_context)

        # if doc_text:
        #     system_message += (
        #         "\n\n"
        #         + f"""
        # The user is currently looking at this document:

        # ```sql
        # {doc_text}
        # ```
        # and may reference it in their questions. If they speak about a query or statement,
        # and it's not referring to something in the chat history, assume they are
        # referring to the query or statement in this document.
        # """.strip()
        #     )

        history.add_system_message(system_message)

        for message in params.history or []:
            if message.participant == "user":
                history.add_user_message(message.content)
            else:
                history.add_assistant_message(message.content)

        # Add prompt as last user input
        if params.prompt:
            history.add_user_message(params.prompt)

        # arguments = KernelArguments(settings=execution_settings)
        # arguments["user_input"] = params.prompt
        # arguments["chat_history"] = history

        request_context.send_response(chat_id)

        async def process_response_stream() -> None:
            # if self._logger:
            #     self._logger.info(f"Processing chat response stream for chat id: {local_chat_id}")
            try:
                async for item in chat_completion.get_streaming_chat_message_contents(
                    history, execution_settings, kernel=kernel
                ):
                    # self._logger.info(f"    {item}")
                    # if is_complete:
                    #     continue

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
                                # self._logger.info(f"    SENDING NOTIFICATION: {content}")
                                request_context.send_notification(
                                    CHAT_COMPLETION_RESULT_METHOD,
                                    ChatCompletionResult.response_part(
                                        chat_id=chat_id,
                                        role=message.role,
                                        content=content,
                                    ),
                                )
                                # self._logger.info("    NOTIFICATION SENT")
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Error processing completion: {e}")
                request_context.send_error(str(e))
                request_context.send_notification(
                    "chat/completion-result",
                    ChatCompletionResult.error(chat_id, str(e)),
                )
                raise

        self._service_provider.async_runner.run(process_response_stream())
