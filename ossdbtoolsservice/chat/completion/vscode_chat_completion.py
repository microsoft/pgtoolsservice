# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections.abc import AsyncGenerator, Mapping
from logging import Logger
from typing import Any, Callable, ClassVar, Union, cast

from pydantic import BaseModel
from semantic_kernel.connectors.ai.chat_completion_client_base import (
    ChatCompletionClientBase,
)
from semantic_kernel.connectors.ai.function_call_choice_configuration import (
    FunctionCallChoiceConfiguration,
)
from semantic_kernel.connectors.ai.function_choice_type import FunctionChoiceType
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
from semantic_kernel.contents import (
    AuthorRole,
    ChatHistory,
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
    StreamingChatMessageContent,
    StreamingTextContent,
    TextContent,
)

from ossdbtoolsservice.chat.prompts import tool_call_to_system_message_prompt

from .completion_response_queues import CompletionResponseQueues
from .messages import (
    VSCODE_LM_CHAT_COMPLETION_REQUEST_METHOD,
    VSCodeLanguageModelChatMessage,
    VSCodeLanguageModelChatMessageRole,
    VSCodeLanguageModelChatTool,
    VSCodeLanguageModelCompleteResultPart,
    VSCodeLanguageModelCompletionRequestParams,
    VSCodeLanguageModelFinishReason,
    VSCodeLanguageModelTextPart,
    VSCodeLanguageModelToolCallPart,
    VSCodeLanguageModelToolResultPart,
)
from .vscode_chat_prompt_execution_settings import VSCodeChatPromptExecutionSettings


class VSCodeChatCompletion(ChatCompletionClientBase):
    """
    An implementation of a ChatCompletionClient that uses Language Server Protocol (LSP)
    JSON-RPC messages to communicate with the VSCode Lamange Model (vscode.lm) API.
    This class allows Semantic Kernel to leverage GitHub Copilot LLMs in chat responses.

    Completion requests are sent to VSCode via LSP notifications, at which time the
    code here starts listening for LSP notifications that are streaming responses from
    the Language Model call. These responses are translated and handled by Semantic Kernel,
    including tool calls.
    """

    SUPPORTS_FUNCTION_CALLING: ClassVar[bool] = True

    _chat_id: str
    _send_request: Callable[[str, BaseModel], None]
    _response_queues: CompletionResponseQueues
    _logger: Logger | None
    _history_translator: "VSCodeChatCompletionHistoryTranslator"

    def __init__(
        self,
        chat_id: str,
        send_request: Callable[[str, BaseModel], None],
        response_queues: CompletionResponseQueues,
        logger: Logger | None = None,
        service_id: str | None = None,
    ):
        """
        Constructor for the GHC Chat Completion Client
        """
        super().__init__(
            ai_model_id="vscode-copilot", service_id=service_id or "vscode-copilot"
        )
        self._chat_id = chat_id
        self._send_request = send_request
        self._response_queues = response_queues
        self._logger = logger
        self._history_translator = VSCodeChatCompletionHistoryTranslator(logger)

    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        return VSCodeChatPromptExecutionSettings

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
            # This encodes the tools available to the model
            # in the format that the VSCode LLM expects
            if function_choice_configuration.available_functions and hasattr(
                settings, "tools"
            ):
                settings.tool_choice = type  # type: ignore
                tools: list[VSCodeLanguageModelChatTool] = []
                for f in function_choice_configuration.available_functions:
                    schema: dict[str, Any] = {"type": "object", "properties": {}}
                    for param in f.parameters:
                        schema["properties"][param.name] = param.schema_data
                    tools.append(
                        VSCodeLanguageModelChatTool(
                            name=f.name,
                            description=f.description or "",
                            input_schema=schema,
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
            chat_message_contents (list[ChatMessageContent]):
                The chat message contents representing the response(s).
        """
        raise NotImplementedError("Non-streaming chat completion is not supported.")

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
            function_invoke_attempt:
                The current attempt count for automatically invoking functions.

        Yields:
            streaming_chat_message_contents: The streaming chat message contents.
        """
        if not isinstance(settings, VSCodeChatPromptExecutionSettings):
            settings = self.get_prompt_execution_settings_from_settings(settings)
        assert isinstance(settings, VSCodeChatPromptExecutionSettings)

        # Create the response queue
        request_id, queue = self._response_queues.register_new_queue()

        try:
            # Translate the request params
            # messages = self._translate_chat_history(chat_history)
            messages = self._history_translator.translate_chat_history(chat_history)

            # Set in _update_function_choice_settings_callback
            tools: list[VSCodeLanguageModelChatTool] = settings.tools or []  # type: ignore

            if not tools:
                # TODO: Remove. I just don't want to miss this case if it happens.
                raise Exception("DEBUG: No tools available for the model")

            # TODO: Model options should be controlled by VSCode?
            model_options: dict[str, Any] = {}

            request = VSCodeLanguageModelCompletionRequestParams(
                chat_id=self._chat_id,
                request_id=request_id,
                messages=messages,
                tools=tools,
                model_options=model_options,
            )

            # Send the request
            self._send_request(VSCODE_LM_CHAT_COMPLETION_REQUEST_METHOD, request)

            # Consume from response queue
            while True:
                finished = False

                # Get the next response
                response = await queue.get()

                transformed_response, finished = self._translate_response(response)
                transformed_response.function_invoke_attempt = function_invoke_attempt

                # TODO: Check if it's a tool call past the maximum allowed, and
                # inform model that's it hit its limit. OR system prompt the max.

                # Yield the response
                yield [transformed_response]

                # Check for completion
                if finished:
                    # Break the loop
                    break

        finally:
            # Delete the response queue
            self._response_queues.delete_queue(request_id)

    def _translate_response(self, response: Any) -> tuple[StreamingChatMessageContent, bool]:
        """Translate response to StreamingChatMessageContent format."""
        finished = False
        if isinstance(response, VSCodeLanguageModelTextPart):
            transformed_response = StreamingChatMessageContent(
                role=AuthorRole.ASSISTANT,
                choice_index=0,
                items=[StreamingTextContent(text=response.value, choice_index=0)],
                inner_content=response,
                finish_reason=None,
            )
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
        elif isinstance(response, VSCodeLanguageModelCompleteResultPart):
            if response.finish_reason == VSCodeLanguageModelFinishReason.ERROR:
                raise RuntimeError(response.error_message)

            transformed_response = StreamingChatMessageContent(
                role=AuthorRole.ASSISTANT,
                choice_index=0,
                items=[],
                inner_content=response,
                finish_reason=response.finish_reason.to_sk_finish_reason(),
            )
            finished = True
        else:
            raise RuntimeError(f"Unexpected response type: {type(response)}: {response}")

        return transformed_response, finished


class VSCodeChatCompletionHistoryTranslator:
    """A class to translate chat history to VSCodeLanguageModelChatMessage format.

    Extracted to class for testability
    """

    def __init__(self, logger: Logger | None = None) -> None:
        self._logger = logger

    def translate_chat_history(
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
                if isinstance(item, TextContent):
                    text = item.text
                    if message.role == AuthorRole.SYSTEM:
                        text = f"<SYSTEM_MESSAGE>{text}</SYSTEM_MESSAGE>"
                    content.append(VSCodeLanguageModelTextPart(value=text))
                elif isinstance(item, FunctionCallContent):
                    id = item.id
                    name = item.name
                    input: dict[str, Any] = {}
                    if item.arguments and isinstance(item.arguments, Mapping):
                        input = {k: v for k, v in item.arguments.items()}

                    if id and name:
                        content.append(
                            VSCodeLanguageModelToolCallPart(
                                call_id=id,
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
                            call_id=item.id,
                            content=[VSCodeLanguageModelTextPart(value=str(item.result))],
                        )
                    )
                else:
                    raise RuntimeError(f"Unexpected item type: {type(item)}: {item}")

            # Post-process content
            processed_content = self._post_process_content(content)

            for content in processed_content:
                if content:
                    messages.append(
                        VSCodeLanguageModelChatMessage(role=role, content=content)
                    )

        # Post-process messages
        return self._post_process_messages(messages)

    def _post_process_content(
        self,
        content: list[
            Union[
                VSCodeLanguageModelTextPart,
                VSCodeLanguageModelToolResultPart,
                VSCodeLanguageModelToolCallPart,
            ]
        ],
    ) -> list[
        list[
            Union[
                VSCodeLanguageModelTextPart,
                VSCodeLanguageModelToolResultPart,
                VSCodeLanguageModelToolCallPart,
            ]
        ]
    ]:
        """Post-process content to separate tool calls into their own messages."""

        # I've found that having assistant text content mixed with tool call content
        # will cause the VSCode sendRequest to fail with
        # "Invalid request: Tool call part must be followed by a User message with
        # a LanguageModelToolResultPart with a matching callId."
        # ...even though the tool result part is given as the next User message.
        # Separate out tool call requests into their own User message,
        # followed by a User message with the tool result part.

        processed_content: list[
            list[
                Union[
                    VSCodeLanguageModelTextPart,
                    VSCodeLanguageModelToolResultPart,
                    VSCodeLanguageModelToolCallPart,
                ]
            ]
        ] = [[]]
        for item in content:
            if isinstance(item, VSCodeLanguageModelToolCallPart):
                processed_content.append([item])
                processed_content.append([])
            else:
                processed_content[-1].append(item)
        return processed_content

    def _post_process_messages(
        self, messages: list[VSCodeLanguageModelChatMessage]
    ) -> list[VSCodeLanguageModelChatMessage]:
        """Post-process messages to ensure tool calls are followed by their results."""

        # There can be multiple tool calls that end up with tool results following
        # in the message history, but not directly after the tool call message.
        # This will cause the VSCode sendRequest to fail.
        # Each tool call message must be followed by the tool result message.
        # Detect tool calls not followed by a tool result, and re-order so tool calls
        # are followed by their results, preserving the order of the tool calls.

        tool_call_index: dict[str, dict[str, VSCodeLanguageModelChatMessage]] = {}
        reordered_messages_staged: list[
            VSCodeLanguageModelChatMessage | dict[str, VSCodeLanguageModelChatMessage]
        ] = []
        for message in messages:
            if message.content and isinstance(
                message.content[0], VSCodeLanguageModelToolCallPart
            ):
                call_id = message.content[0].call_id
                if call_id in tool_call_index:
                    raise RuntimeError(f"Tool call with callId {call_id} already exists")
                else:
                    d = {"call": message}
                    tool_call_index[call_id] = d
                    reordered_messages_staged.append(d)
            elif message.content and isinstance(
                message.content[0], VSCodeLanguageModelToolResultPart
            ):
                call_id = message.content[0].call_id
                if call_id in tool_call_index:
                    tool_call_index[call_id]["result"] = message
                else:
                    raise RuntimeError(
                        f"Tool result with callId {call_id} "
                        "does not have a matching tool call"
                    )
            else:
                reordered_messages_staged.append(message)

        # Determine index of the last user (non-tool) message.
        last_user_index = -1
        for idx, item in enumerate(reordered_messages_staged):
            if not isinstance(item, dict):
                last_user_index = idx

        reordered_messages: list[VSCodeLanguageModelChatMessage] = []
        for i, item in enumerate(reordered_messages_staged):
            if isinstance(item, dict):
                if last_user_index != -1 and i < last_user_index:
                    # Tool calls in history are not allowed by VSCode.
                    # For each tool call that is before the last user message,
                    # translate them to a system message.
                    call = cast(VSCodeLanguageModelToolCallPart, item["call"].content[0])
                    result = cast(
                        VSCodeLanguageModelToolResultPart, item["result"].content[0]
                    )
                    tool_call_prompt = tool_call_to_system_message_prompt(
                        call_id=call.call_id,
                        function_name=call.name,
                        function_input=call.input,
                        result=result.content[0].value,
                    )
                    reordered_messages.append(
                        VSCodeLanguageModelChatMessage(
                            role=VSCodeLanguageModelChatMessageRole.USER,
                            content=[VSCodeLanguageModelTextPart(value=tool_call_prompt)],
                        )
                    )
                else:
                    # Append tool call/result pairs as separate messages.
                    reordered_messages.append(item["call"])
                    reordered_messages.append(item["result"])
            else:
                reordered_messages.append(item)

        return reordered_messages
