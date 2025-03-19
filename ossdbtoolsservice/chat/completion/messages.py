from enum import Enum
from typing import Any, Union

from semantic_kernel.contents.utils.finish_reason import FinishReason

from ossdbtoolsservice.core.models import PGTSBaseModel
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


class VSCodeLanguageModelTextPart(PGTSBaseModel):
    value: str


class VSCodeLanguageModelToolCallPart(PGTSBaseModel):
    call_id: str
    name: str
    input: dict[str, Any]


class VSCodeLanguageModelToolResultPart(PGTSBaseModel):
    call_id: str
    content: list[VSCodeLanguageModelTextPart]


class VSCodeLanguageModelCompleteResultPart(PGTSBaseModel):
    error_message: str | None = None
    finish_reason: VSCodeLanguageModelFinishReason


# Request


class VSCodeLanguageModelChatMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class VSCodeLanguageModelChatMessage(PGTSBaseModel):
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


class VSCodeLanguageModelChatTool(PGTSBaseModel):
    name: str
    description: str
    input_schema: dict[str, Any]
    """A JSON schema for the input this tool accepts."""


class VSCodeLanguageModelCompletionRequestParams(PGTSBaseModel):
    chat_id: str
    request_id: str
    messages: list[VSCodeLanguageModelChatMessage]
    model_options: dict[str, Any]
    tools: list[VSCodeLanguageModelChatTool]
    justification: str | None = None


# Response


class VSCodeLanguageModelChatCompletionResponse(PGTSBaseModel):
    request_id: str
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
