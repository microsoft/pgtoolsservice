# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from logging import Logger

from semantic_kernel.connectors.ai import (
    PromptExecutionSettings,
)
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.contents import (
    AuthorRole,
    FunctionCallContent,
    FunctionResultContent,
    TextContent,
)
from semantic_kernel.kernel import Kernel

from ossdbtoolsservice.chat.chat_history_manager import ChatHistoryManager
from ossdbtoolsservice.chat.completion.vscode_chat_prompt_execution_settings import (
    VSCodeChatPromptExecutionSettings,
)
from ossdbtoolsservice.chat.messages import (
    CHAT_COMPLETION_RESULT_METHOD,
    CHAT_REQUEST,
    ChatCompletionContent,
    ChatCompletionRequestParams,
    ChatCompletionRequestResult,
)
from ossdbtoolsservice.chat.plugin.azure_pg.azure_pg_plugin import AzurePGPlugin
from ossdbtoolsservice.chat.plugin.docs_plugin import DocsPlugin
from ossdbtoolsservice.chat.plugin.plugin_base import PGTSChatPlugin
from ossdbtoolsservice.connection.connection_service import ConnectionService
from ossdbtoolsservice.hosting import Service, ServiceProvider
from ossdbtoolsservice.hosting.context import NotificationContext, RequestContext
from ossdbtoolsservice.hosting.message_server import MessageServer
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.utils.async_runner import AsyncRunner
from ossdbtoolsservice.workspace.workspace_service import WorkspaceService

from .completion.completion_response_queues import CompletionResponseQueues
from .completion.messages import (
    VSCODE_LM_COMPLETION_RESPONSE,
    VSCodeLanguageModelChatCompletionResponse,
)
from .completion.vscode_chat_completion import VSCodeChatCompletion
from .plugin.postgres_plugin import PostgresPlugin
from .prompts import system_message_prompt


class ChatService(Service):
    def __init__(
        self,
        chat_completion: ChatCompletionClientBase | None = None,
        execution_settings: PromptExecutionSettings | None = None,
    ) -> None:
        self._service_provider: ServiceProvider | None = None
        self._server: MessageServer | None = None
        self._logger: Logger | None = None

        # Mapping of completion request IDs to Queues
        self.completion_response_queues = CompletionResponseQueues()

        self._chat_completion = chat_completion
        self._prompt_execution_settings = execution_settings
        if self._chat_completion is None and os.environ.get("PGTS_CHAT_USE_AZURE_OPENAI"):
            # Allow Azure OpenAI to be used with environment variables
            self._chat_completion = AzureChatCompletion()
            if self._prompt_execution_settings is None:
                self._prompt_execution_settings = AzureChatPromptExecutionSettings(
                    function_choice_behavior=FunctionChoiceBehavior.Auto(),
                    max_tokens=7000,
                    temperature=0.7,
                    top_p=0.8,
                )

        if self._chat_completion is not None and self._prompt_execution_settings is None:
            raise ValueError(
                "Must supply prompt execution settings if supplying chat completion"
            )

        self.executor = ThreadPoolExecutor(max_workers=10)

        self._chat_history_manager = ChatHistoryManager()

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
            VSCODE_LM_COMPLETION_RESPONSE, self._handle_completion_response_notification
        )

        if self._service_provider.logger is not None:
            self._service_provider.logger.info("Chat service successfully initialized")

    def _handle_completion_response_notification(
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

        session_id = params.session_id

        doc_text, selected_doc_text = self._get_active_document_text(params)

        kernel = Kernel()

        chat_completion: ChatCompletionClientBase
        execution_settings: PromptExecutionSettings
        if not self._chat_completion:
            chat_completion = VSCodeChatCompletion(
                chat_id,
                request_context.send_notification,
                self.completion_response_queues,
                logger=self._logger,
            )
            # In VSCode, temperature, top_p etc are set in the extension
            execution_settings = VSCodeChatPromptExecutionSettings(
                function_choice_behavior=FunctionChoiceBehavior.Auto(
                    maximum_auto_invoke_attempts=10  # TODO: How best to configure?
                ),
            )
        else:
            assert self._prompt_execution_settings is not None  # Validated in __init__
            chat_completion = self._chat_completion
            execution_settings = self._prompt_execution_settings

        kernel.add_service(chat_completion)

        connection_service = self._service_provider.get(
            constants.CONNECTION_SERVICE_NAME, ConnectionService
        )
        connection_info = connection_service.get_connection_info(owner_uri)
        if connection_info is None:
            request_context.send_error(f"Connection info not found for {owner_uri}")
            return
        is_azure_pg = connection_info.connection_details.is_azure_pg

        plugins: list[PGTSChatPlugin] = [
            PostgresPlugin(
                connection_service=connection_service,
                request_context=request_context,
                chat_id=chat_id,
                profile_name=params.profile_name,
                copilot_access_mode=params.access_mode,
                owner_uri=owner_uri,
                logger=self._logger,
            )
        ]
        if is_azure_pg:
            plugins.append(
                AzurePGPlugin(
                    request_context=request_context,
                    chat_id=chat_id,
                    subscription_id=connection_info.connection_details.azure_subscription_id,
                    resource_group=connection_info.connection_details.azure_resource_group,
                    server_name=connection_info.connection_details.server_name,
                    database_name=connection_info.connection_details.database_name,
                    arm_token=params.arm_token.token if params.arm_token else None,
                    logger=self._logger,
                )
            )

        docs_plugin = DocsPlugin(
            request_context=request_context, chat_id=chat_id, logger=self._logger
        )
        for plugin in plugins:
            for doc in plugin.topic_documentation:
                docs_plugin.add_topic_documentation(doc)
        plugins.append(docs_plugin)

        for plugin in plugins:
            plugin.add_to(kernel)

        # Fetch schemas and tables to be injected into the system message
        # db_context = postgres_plugin.get_db_context()
        db_context = None
        system_message = system_message_prompt(
            doc_text=doc_text,
            selected_doc_text=selected_doc_text,
            db_context=db_context,
            profile_name=params.profile_name,
            is_azure_pg=is_azure_pg,
            result_messages=params.result_messages,
        )

        history = self._chat_history_manager.get_chat_history(
            session_id=session_id,
            request_prompt=params.prompt,
            request_history=params.history,
            system_message=system_message,
        )

        request_context.send_response(ChatCompletionRequestResult(chat_id=chat_id))

        async def process_response_stream() -> None:
            try:
                async for item in chat_completion.get_streaming_chat_message_contents(
                    history, execution_settings, kernel=kernel
                ):
                    for message in item:
                        if message.finish_reason == "stop":
                            request_context.send_notification(
                                CHAT_COMPLETION_RESULT_METHOD,
                                ChatCompletionContent.complete(
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
                                    ChatCompletionContent.response_part(
                                        chat_id=chat_id,
                                        role=message.role,
                                        content=content,
                                    ),
                                )

                # Get function call content out of history
                if session_id:
                    last_user_message: str | None = None
                    tool_calls: dict[str, FunctionCallContent] = {}
                    for message in history.messages:
                        if message.role == AuthorRole.USER and message.content:
                            last_user_message = message.content
                        elif (
                            message.role == AuthorRole.ASSISTANT
                            or message.role == AuthorRole.TOOL
                        ):
                            for content in message.items:
                                if isinstance(content, FunctionCallContent) and content.id:
                                    tool_calls[content.id] = content
                                elif (
                                    isinstance(content, FunctionResultContent)
                                    and content.id in tool_calls
                                    and last_user_message
                                ):
                                    self._chat_history_manager.add_tool_call_record(
                                        session_id,
                                        last_user_message,
                                        tool_calls[content.id],
                                        content,
                                    )
            except Exception as e:
                if self._logger:
                    self._logger.exception(e)
                    self._logger.error(f"Error processing completion: {e}")
                request_context.send_error(str(e))
                request_context.send_notification(
                    CHAT_COMPLETION_RESULT_METHOD,
                    ChatCompletionContent.error(chat_id, str(e)),
                )
                raise

        try:
            self.get_async_runner().run(process_response_stream())
        except Exception as e:
            if self._logger:
                self._logger.exception(e)
                self._logger.error(f"Error in chat request: {e}")
            request_context.send_notification(
                CHAT_COMPLETION_RESULT_METHOD,
                ChatCompletionContent.error(chat_id, str(e)),
            )

    def _get_active_document_text(
        self, params: ChatCompletionRequestParams
    ) -> tuple[str | None, str | None]:
        doc_text: str | None = None
        selected_doc_text: str | None = None
        if params.active_editor_uri:
            workspace_service = self.service_provider.get(
                constants.WORKSPACE_SERVICE_NAME, WorkspaceService
            )
            doc_text = workspace_service.get_text(
                params.active_editor_uri, selection_range=None
            )
            if params.active_editor_selection:
                selection_range = (
                    params.active_editor_selection.to_range()
                    if params.active_editor_selection is not None
                    else None
                )

                selected_doc_text = workspace_service.get_text(
                    params.active_editor_uri, selection_range
                )

        return doc_text, selected_doc_text
