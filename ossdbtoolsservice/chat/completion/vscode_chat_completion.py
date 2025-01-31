# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import sys
from collections.abc import Mapping
import functools
from logging import Logger
from typing import Any, AsyncGenerator, Callable, ClassVar, Union
from pydantic import BaseModel
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
from semantic_kernel.connectors.ai.function_call_choice_configuration import (
    FunctionCallChoiceConfiguration,
)
from semantic_kernel.connectors.ai.function_choice_type import FunctionChoiceType
from semantic_kernel.contents import (
    AuthorRole,
    ChatHistory,
    ChatMessageContent,
    StreamingChatMessageContent,
    StreamingTextContent,
    FunctionCallContent,
    FunctionResultContent,
    FinishReason,
)

from .completion_response_queues import CompletionResponseQueues
from .messages import (
    VSCODE_LM_CHAT_COMPLETION_REQUEST_METHOD,
    VSCodeLanguageModelChatMessage,
    VSCodeLanguageModelChatMessageRole,
    VSCodeLanguageModelChatTool,
    VSCodeLanguageModelCompletionRequestParams,
    VSCodeLanguageModelTextPart,
    VSCodeLanguageModelToolCallPart,
    VSCodeLanguageModelCompleteResultPart,
    VSCodeLanguageModelToolResultPart,
)
from .vscode_chat_prompt_execution_settings import VSCodeChatPromptExecutionSettings

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class VSCodeChatCompletion(ChatCompletionClientBase):
    """
    A class to interact with the VS Code GitHub Copilot LLMs
    """

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

    def __init__(
        self,
        send_request: Callable[[str, BaseModel], None],
        response_queues: CompletionResponseQueues,
        logger: Logger | None = None,
    ):
        """
        Constructor for the GHC Chat Completion Client
        """
        self._send_request = send_request
        self._response_queues = response_queues
        self._logger = logger

    @override
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return VSCodeChatPromptExecutionSettings

    @override
    def _update_function_choice_settings_callback(
        self,
    ) -> Callable[
        [
            FunctionCallChoiceConfiguration,
            "PromptExecutionSettings",
            FunctionChoiceType,
        ],
        None,
    ]:
        def update_settings_from_function_call_configuration(
            function_choice_configuration: "FunctionCallChoiceConfiguration",
            settings: "PromptExecutionSettings",
            type: "FunctionChoiceType",
        ) -> None:
            """Update the settings from a FunctionChoiceConfiguration."""
            if (
                function_choice_configuration.available_functions
                and hasattr(settings, "tool_choice")
                and hasattr(settings, "tools")
            ):
                settings.tool_choice = type  # type: ignore
                tools: list[VSCodeLanguageModelChatTool] = []
                for f in function_choice_configuration.available_functions:
                    schema = {"type": "object", "properties": {}}
                    for param in f.parameters:
                        schema["properties"][param.name] = param.schema_data
                    tools.append(
                        VSCodeLanguageModelChatTool(
                            name=f.name,
                            description=f.description or "",
                            inputSchema=schema,
                        )
                    )
                settings.tools = tools  # type: ignore

        return update_settings_from_function_call_configuration

    async def _inner_get_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: PromptExecutionSettings,
    ) -> list[ChatMessageContent]:
        """Send a chat request to the AI service.

        Args:
            chat_history (ChatHistory): The chat history to send.
            settings (PromptExecutionSettings): The settings for the request.

        Returns:
            chat_message_contents (list[ChatMessageContent]): The chat message contents representing the response(s).
        """
        # Use _inner_get_streaming_chat_message_contents
        result: list[ChatMessageContent] = []
        async for (
            streaming_chat_message_contents
        ) in self._inner_get_streaming_chat_message_contents(chat_history, settings):
            reduced = functools.reduce(
                lambda a, b: a + b, streaming_chat_message_contents
            )
            result.append(
                ChatMessageContent(
                    role=reduced.role,
                    content=reduced.content,
                    inner_content=reduced.inner_content,
                    finish_reason=reduced.finish_reason,
                )
            )
        return result

    async def _inner_get_streaming_chat_message_contents(
        self,
        chat_history: ChatHistory,
        settings: PromptExecutionSettings,
        function_invoke_attempt: int = 0,
    ) -> AsyncGenerator[list[StreamingChatMessageContent], Any]:
        """Send a streaming chat request to the AI service.

        Args:
            chat_history: The chat history to send.
            settings: The settings for the request.
            function_invoke_attempt: The current attempt count for automatically invoking functions.

        Yields:
            streaming_chat_message_contents: The streaming chat message contents.
        """
        if not isinstance(settings, VSCodeChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, VSCodeChatPromptExecutionSettings)  # nosec

        # Create the response queue
        request_id, queue = self._response_queues.register_new_qeue()

        try:
            # Translate the request params
            messages = self._translate_chat_history(chat_history)

            # Set in _update_function_choice_settings_callback
            tools: list[VSCodeLanguageModelChatTool] = settings.tools  # type: ignore

            # TODO: Model options should be controlled by VSCode?
            model_options: dict[str, Any] = {}

            request = VSCodeLanguageModelCompletionRequestParams(
                requestId=request_id,
                messages=messages,
                tools=tools,
                modelOptions=model_options,
            )

            # Send the request
            self._send_request(VSCODE_LM_CHAT_COMPLETION_REQUEST_METHOD, request)

            # Consume from response queue
            while True:
                finished = False

                # Get the next response
                response = queue.get()

                transformed_response, finished = self._translate_response(response)

                # Yield the response
                yield [transformed_response]

                # Check for completion
                if finished:
                    # Break the loop
                    break

        finally:
            # Delete the response queue
            self._response_queues.delete_queue(request_id)

    def _translate_response(
        self, response: Any
    ) -> tuple[StreamingChatMessageContent, bool]:
        """Translate response to StreamingChatMessageContent format."""
        if isinstance(response, VSCodeLanguageModelTextPart):
            transformed_response = StreamingChatMessageContent(
                role=AuthorRole.ASSISTANT,
                choice_index=0,
                items=[StreamingTextContent(text=response.value, choice_index=0)],
                inner_content=response,
                finish_reason=None,
            )
            finished = False
        elif isinstance(response, VSCodeLanguageModelToolCallPart):
            transformed_response = StreamingChatMessageContent(
                role=AuthorRole.ASSISTANT,
                choice_index=0,
                items=[
                    FunctionCallContent(
                        id=response.call_id,
                        index=0,
                        name=response.name,
                        arguments=response.input,
                    )
                ],
                inner_content=response,
                finish_reason=None,
            )
            finished = False
        elif isinstance(response, VSCodeLanguageModelCompleteResultPart):
            if response.is_error:
                raise RuntimeError(response.error_message)

            transformed_response = StreamingChatMessageContent(
                role=AuthorRole.ASSISTANT,
                choice_index=0,
                items=[],
                inner_content=response,
                finish_reason=FinishReason.STOP,
            )
            finished = True
        else:
            raise RuntimeError(
                f"Unexpected response type: {type(response)}: {response}"
            )

        return transformed_response, finished

    def _translate_chat_history(
        self, chat_history: ChatHistory
    ) -> list[VSCodeLanguageModelChatMessage]:
        """Translate chat history to VSCodeLanguageModelChatMessage format."""
        messages: list[VSCodeLanguageModelChatMessage] = []
        for message in chat_history.messages:
            role = VSCodeLanguageModelChatMessageRole.USER
            if message.role == AuthorRole.ASSISTANT:
                role = VSCodeLanguageModelChatMessageRole.ASSISTANT

            content: list[
                Union[
                    VSCodeLanguageModelTextPart,
                    VSCodeLanguageModelToolResultPart,
                    VSCodeLanguageModelToolCallPart,
                ]
            ] = []
            for item in message.items:
                if isinstance(item, StreamingTextContent):
                    text = item.text
                    if message.role == AuthorRole.SYSTEM:
                        text = f"__System Prompt__: {text}"
                    content.append(VSCodeLanguageModelTextPart(value=text))
                elif isinstance(item, FunctionCallContent):
                    id = item.id
                    name = item.name
                    input: dict[str, Any] = {}
                    if item.arguments:
                        if isinstance(item.arguments, Mapping):
                            input = {k: v for k, v in item.arguments.items()}

                    if id and name:
                        content.append(
                            VSCodeLanguageModelToolCallPart(
                                callId=id,
                                name=name,
                                input=input,
                            )
                        )
                    else:
                        if self._logger:
                            self._logger.error(
                                "Function call content must have an id and name"
                            )
                elif isinstance(item, FunctionResultContent):
                    content.append(
                        VSCodeLanguageModelToolResultPart(
                            callId=item.id,
                            content=[
                                VSCodeLanguageModelTextPart(value=str(item.result))
                            ],
                        )
                    )
                else:
                    raise RuntimeError(f"Unexpected item type: {type(item)}: {item}")

            messages.append(VSCodeLanguageModelChatMessage(role=role, content=content))
        return messages
