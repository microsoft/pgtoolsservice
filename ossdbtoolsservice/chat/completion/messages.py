from enum import Enum
from typing import Any, Union

from pydantic import BaseModel, Field
from semantic_kernel.contents.utils.finish_reason import FinishReason

from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)


class VSCodeLanguageModelFinishReason(str, Enum):
    """Finish Reason enum."""

    STOP = "stop"
    CONTENT_FILTER = "content_filter"
    TOOL_CALLS = "tool_calls"
    ERROR = "error"

    def to_sk_finish_reason(self) -> FinishReason:
        """Converts the VSCodeLanguageModelFinishReason to a Semantic Kernel FinishReason."""
        if self == VSCodeLanguageModelFinishReason.ERROR:
            # This doen'st have a mapping, and should be handled by error handling elsewhere.
            # Just use STOP.
            return FinishReason.STOP
        return FinishReason(self.value)


# Requests

VSCODE_LM_CHAT_COMPLETION_REQUEST_METHOD = "chat/vscode-lm-completion-request"

# Notifications

VSCODE_LM_COMPLETION_RESPONSE_METHOD = "chat/vscode-lm-response"

# Content


class VSCodeLanguageModelTextPart(BaseModel):
    value: str


class VSCodeLanguageModelToolCallPart(BaseModel):
    call_id: str = Field(alias="callId")
    name: str
    input: dict[str, Any]


class VSCodeLanguageModelToolResultPart(BaseModel):
    call_id: str = Field(alias="callId")
    content: list[VSCodeLanguageModelTextPart]


class VSCodeLanguageModelCompleteResultPart(BaseModel):
    error_message: str | None = Field(default=None, alias="errorMessage")
    finish_reason: VSCodeLanguageModelFinishReason = Field(alias="finishReason")


# Request


class VSCodeLanguageModelChatMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class VSCodeLanguageModelChatMessage(BaseModel):
    role: VSCodeLanguageModelChatMessageRole
    """The role of this message"""

    name: str | None = None
    """The optional name of a user for this message."""

    content: list[
        Union[
            VSCodeLanguageModelTextPart,
            VSCodeLanguageModelToolResultPart,
            VSCodeLanguageModelToolCallPart,
        ]
    ]
    """A string or heterogeneous array of things that a message can contain as content. 
    Some parts may be message-type specific for some models."""


class VSCodeLanguageModelChatTool(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = Field(alias="inputSchema")
    """A JSON schema for the input this tool accepts."""


class VSCodeLanguageModelCompletionRequestParams(BaseModel):
    chat_id: str = Field(alias="chatId")
    request_id: str = Field(alias="requestId")
    messages: list[VSCodeLanguageModelChatMessage]
    model_options: dict[str, Any] = Field(alias="modelOptions")
    tools: list[VSCodeLanguageModelChatTool]
    justification: str | None = None


# Response


class VSCodeLanguageModelChatCompletionResponse(BaseModel):
    request_id: str = Field(alias="requestId")
    response: (
        VSCodeLanguageModelCompleteResultPart
        | VSCodeLanguageModelTextPart
        | VSCodeLanguageModelToolCallPart
    )


# Configs

VSCODE_LM_CHAT_COMPLETION_REQUEST = OutgoingMessageRegistration.register_outgoing_message(
    VSCodeLanguageModelCompletionRequestParams
)

VSCODE_LM_COMPLETION_RESPONSE = IncomingMessageConfiguration(
    VSCODE_LM_COMPLETION_RESPONSE_METHOD, VSCodeLanguageModelChatCompletionResponse
)
