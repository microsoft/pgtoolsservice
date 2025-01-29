# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import AsyncGenerator
import uuid
from logging import Logger

from openai import chat
from semantic_kernel import Kernel
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.chat.messages import (
    CHAT_REQUEST,
    ChatCompletionRequestParams,
    ChatCompletionResult,
)
from ossdbtoolsservice.hosting import RequestContext, ServiceProvider, JSONRPCServer

from rich.console import Console
from rich.markdown import Markdown
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
)
from semantic_kernel.connectors.memory.postgres import PostgresSettings
from semantic_kernel.contents import ChatHistory, StreamingChatMessageContent
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.contents.text_content import TextContent

from .entra_connection import AsyncEntraConnection
from .plugin.postgres_plugin import PostgresPlugin


class ChatService(object):
    def __init__(self):
        self._service_provider: ServiceProvider = None
        self._server: JSONRPCServer = None
        self._logger: Logger = None

        self._service_action_mapping: dict = {
            CHAT_REQUEST: self._handle_chat_request,
        }

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider
        self._server = service_provider.server
        self._logger = service_provider.logger

        # Register the request handlers with the server
        for action in self._service_action_mapping:
            self._service_provider.server.set_request_handler(
                action, self._service_action_mapping[action]
            )

        if self._service_provider.logger is not None:
            self._service_provider.logger.info("Chat service successfully initialized")

    def _handle_chat_request(
        self, request_context: RequestContext, params: ChatCompletionRequestParams
    ):
        chat_id = str(uuid.uuid4())
        if self._logger:
            self._logger.info(f"Chat request received with id: {chat_id}")

        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("owner_uri is required")
            return

        kernel = Kernel()

        import os

        os.environ["AZURE_OPENAI_API_VERSION"] = "2023-05-15"
        os.environ["AZURE_OPENAI_ENDPOINT"] = (
            "https://oai-rde-dev-eastus.openai.azure.com"
        )
        os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"] = "gpt-4o-mini"
        # AZURE_OPENAI_CHAT_DEPLOYMENT_NAME="gpt-4o-mini"
        os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"] = "text-embedding-3-small"
        # AZURE_OPENAI_text_to_image_deployment_name="text-to-image-ada-002"
        os.environ["AZURE_OPENAI_API_KEY"] = "13eca0a59d4c469fbcc0869bdf40d478"

        # Add the AzureChatCompletion service, which will be used to generate completions for the chat.
        chat_completion = AzureChatCompletion(service_id="chat")
        kernel.add_service(chat_completion)

        # chat_function = kernel.add_function(
        #     prompt="{{$chat_history}}{{$user_input}}",
        #     plugin_name="ChatBot",
        #     function_name="Chat",
        # )

        connection_service = self._service_provider[constants.CONNECTION_SERVICE_NAME]
        PostgresPlugin(connection_service, owner_uri, self._logger).add_to(kernel)

        # we set the function choice to Auto, so that the LLM can choose the correct function to call.
        # and we exclude the ChatBot plugin, so that it does not call itself.
        # this means that it has access to 2 functions, that were defined above.
        execution_settings = AzureChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(
                # filters={"excluded_plugins": ["ChatBot"]}
            ),
            service_id="chat",
            max_tokens=7000,
            temperature=0.7,
            top_p=0.8,
        )

        self._logger.info(f"EXECUTION SETTINGS: {execution_settings.function_choice_behavior.auto_invoke_kernel_functions}")

        history = ChatHistory()
        system_message = """
        You are a chat bot. Your name is Dumbo and
        you have one goal: help people work with their PostgreSQL database.
        Assume that questions about the database schema, tables, columns, and data etc are
        all referring to the user's specific database, and fetch the database context
        before providing an answer.
        If the user's inquiry can be aided by a SQL script, you will provide it in the response.
        You utilize the specific PostgreSQL database context the user has access to whenever possible.
        If the user does not specify a specific schema to work with, you will default to the 'public' schema.
        You are able to execute read-only SQL queries against the user's database. You can execute read-only
         statements arbitrarily.
        For any statement that will modify the database, you should always
        present the query to the user before executing it. Present the query with a name that the user can reference
         when confirming that it should be executed. The user MUST confirm the query BY NAME before it is
        executed.
        """
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

        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        executor = ThreadPoolExecutor()

        def process_response_stream(
            async_gen: AsyncGenerator[list[StreamingChatMessageContent], None],
        ):
            """Runs an async generator in a separate thread and processes values one-by-one."""
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            local_chat_id = chat_id

            async def process():
                # if self._logger:
                #     self._logger.info(f"Processing chat response stream for chat id: {local_chat_id}")
                is_complete = False
                async for item in async_gen:
                    try:
                        # self._logger.info(f"    {item}")
                        # if is_complete:
                        #     continue
                        
                        for message in item:                        
                            is_complete = message.finish_reason == "stop"
                            content="".join(
                                        item.text or "" for item in message.items if isinstance(item, TextContent)
                                    )                        
                            if content or is_complete:
                                self._logger.info(f"    SENDING NOTIFICATION: {content}")
                                request_context.send_notification(
                                    "chat/completion-result",
                                    ChatCompletionResult(
                                        chat_id=local_chat_id,
                                        role=message.role,
                                        content=content,
                                        is_complete=is_complete
                                    ),
                                )
                                self._logger.info("    NOTIFICATION SENT")
                    except Exception as e:
                        if self._logger:
                            self._logger.error(f"Error processing chat response stream: {e}")
                        request_context.send_error(str(e))

            loop.run_until_complete(process())

        executor.submit(
            process_response_stream,
            chat_completion.get_streaming_chat_message_contents(history, execution_settings, kernel=kernel, logger=self._logger)
            # kernel.invoke_stream(chat_function, arguments=arguments),
        )
