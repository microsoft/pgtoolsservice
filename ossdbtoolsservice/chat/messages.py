# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field

from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
)

# Requests
CHAT_COMPLETION_REQUEST_METHOD = "chat/completion-request"

# Notifications
CHAT_PROGRESS_UPDATE_METHOD = "chat/progress-update"
CHAT_COMPLETION_RESULT_METHOD = "chat/completion-result"
COPILOT_QUERY_NOTIFICATION_METHOD = "chat/notify-copilot-query"


class ChatMessageContent(BaseModel):
    participant: str
    content: str


class ChatCompletionRequestParams(BaseModel):
    prompt: str
    history: list[ChatMessageContent]
    owner_uri: str = Field(alias="ownerUri")
    document: str | None = None


class ChatProgressUpdateParams(BaseModel):
    chat_id: str | None = Field(None, alias="chatId")
    content: str | None = None


class CopilotQueryNotificationParams(BaseModel):
    query_name: str = Field(alias="queryName")
    query_description: str = Field(alias="queryDescription")
    query: str
    owner_uri: str = Field(alias="ownerUri")
    has_error: bool = Field(default=False, alias="hasError")


class ChatCompletionResult(BaseModel):
    role: str | None
    content: str | None = None
    chat_id: str = Field(alias="chatId")
    is_complete: bool = Field(False, alias="isComplete")
    complete_reason: str | None = Field(default=None, alias="completeReason")
    is_error: bool = Field(default=False, alias="isError")
    error_message: str | None = Field(default=None, alias="errorMessage")

    model_config = ConfigDict(
        populate_by_name=True,
    )

    @classmethod
    def error(cls, chat_id: str, error_message: str) -> "ChatCompletionResult":
        return cls(
            role=None,
            content=None,
            chatId=chat_id,
            isComplete=True,
            completeReason="error",
            isError=True,
            errorMessage=error_message,
        )

    @classmethod
    def response_part(cls, chat_id: str, role: str, content: str) -> "ChatCompletionResult":
        return cls(
            role=role,
            content=content,
            chatId=chat_id,
            isComplete=False,
            completeReason=None,
            isError=False,
            errorMessage=None,
        )

    @classmethod
    def complete(cls, chat_id: str, reason: str) -> "ChatCompletionResult":
        return cls(
            role=None,
            content=None,
            chatId=chat_id,
            isComplete=True,
            completeReason=reason,
            isError=False,
            errorMessage=None,
        )


CHAT_REQUEST = IncomingMessageConfiguration(
    CHAT_COMPLETION_REQUEST_METHOD, ChatCompletionRequestParams
)
