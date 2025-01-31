from enum import Enum
from typing import Any, Union
from pydantic import BaseModel, Field

from ossdbtoolsservice.hosting.json_rpc_server import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)

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
    is_error: bool = Field(default=False, alias="isError")
    error_message: str | None = Field(default=None, alias="errorMessage")


# Request


class VSCodeLanguageModelChatMessageRole(Enum):
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
    """A string or heterogeneous array of things that a message can contain as content. Some parts may be message-type specific for some models."""


class VSCodeLanguageModelChatTool(BaseModel):
    name: str
    description: str
    input_schema: dict[str, Any] = Field(alias="inputSchema")
    """A JSON schema for the input this tool accepts."""


class VSCodeLanguageModelCompletionRequestParams(BaseModel):
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

VSCODE_LM_CHAT_COMPLETION_REQUEST = (
    OutgoingMessageRegistration.register_outgoing_message(
        VSCodeLanguageModelCompletionRequestParams
    )
)

VSCODE_LM_COMPLETION_RESPONSE = IncomingMessageConfiguration(
    VSCODE_LM_COMPLETION_RESPONSE_METHOD, VSCodeLanguageModelChatCompletionResponse
)
