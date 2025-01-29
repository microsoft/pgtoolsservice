# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import uuid

from semantic_kernel import Kernel
from ossdbtoolsservice.utils import constants
from ossdbtoolsservice.chat.messages import CHAT_REQUEST, ChatCompletionRequestParams
from ossdbtoolsservice.hosting import RequestContext, ServiceProvider

from rich.console import Console
from rich.markdown import Markdown
from semantic_kernel.connectors.ai.function_choice_behavior import (
    FunctionChoiceBehavior,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)
from semantic_kernel.connectors.memory.postgres import PostgresSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel

from .entra_connection import AsyncEntraConnection
from .plugin.postgres_plugin import PostgresPlugin


class ChatService(object):
    def __init__(self):
        self._service_provider: ServiceProvider = None

        self._service_action_mapping: dict = {
            CHAT_REQUEST: self._handle_chat_request,
        }

    def register(self, service_provider: ServiceProvider):
        self._service_provider = service_provider
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
        chat_id = uuid.uuid4()
        owner_uri = params.owner_uri
        if owner_uri is None:
            request_context.send_error("owner_uri is required")
            return

        kernel = Kernel()

        # Add the AzureChatCompletion service, which will be used to generate completions for the chat.
        chat_completion = AzureChatCompletion(
            service_id="chat", deployment_name="gpt-4o"
        )
        kernel.add_service(chat_completion)

        connection_service = self._service_provider[constants.CONNECTION_SERVICE_NAME]
        PostgresPlugin(connection_service, owner_uri).add_to(kernel)

        # we set the function choice to Auto, so that the LLM can choose the correct function to call.
        # and we exclude the ChatBot plugin, so that it does not call itself.
        # this means that it has access to 2 functions, that were defined above.
        execution_settings = AzureChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(
                filters={"excluded_plugins": ["ChatBot"]}
            ),
            service_id="chat",
            max_tokens=7000,
            temperature=0.7,
            top_p=0.8,
        )

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
                history.add_user_message(message)
            else:
                history.add_assistant_message(message)

        arguments = KernelArguments(settings=execution_settings)
        arguments["user_input"] = params.prompt
        arguments["chat_history"] = history

        request_context.send_response(chat_id)

        kernel.invoke_prompt_stream()
