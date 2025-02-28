# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
)

# Requests
CHAT_COMPLETION_REQUEST_METHOD = "chat/completion-request"

# Notifications
CHAT_PROGRESS_UPDATE_METHOD = "chat/progress-update"
CHAT_COMPLETION_RESULT_METHOD = "chat/completion-result"
COPILOT_QUERY_NOTIFICATION_METHOD = "chat/notify-copilot-query"


class ChatMessageContent(PGTSBaseModel):
    participant: str
    content: str


class ChatCompletionRequestParams(PGTSBaseModel):
    prompt: str
    history: list[ChatMessageContent]
    owner_uri: str
    document: str | None = None


class ChatProgressUpdateParams(PGTSBaseModel):
    chat_id: str | None = None
    content: str | None = None


class CopilotQueryNotificationParams(PGTSBaseModel):
    query_name: str
    query_description: str
    query: str
    owner_uri: str
    has_error: bool = False


class ChatCompletionResult(PGTSBaseModel):
    role: str | None
    content: str | None = None
    chat_id: str
    is_complete: bool = False
    complete_reason: str | None = None
    is_error: bool = False
    error_message: str | None = None

    @classmethod
    def error(cls, chat_id: str, error_message: str) -> "ChatCompletionResult":
        return cls(
            role=None,
            content=None,
            chat_id=chat_id,
            is_complete=True,
            complete_reason="error",
            is_error=True,
            error_message=error_message,
        )

    @classmethod
    def response_part(cls, chat_id: str, role: str, content: str) -> "ChatCompletionResult":
        return cls(
            role=role,
            content=content,
            chat_id=chat_id,
            is_complete=False,
            complete_reason=None,
            is_error=False,
            error_message=None,
        )

    @classmethod
    def complete(cls, chat_id: str, reason: str) -> "ChatCompletionResult":
        return cls(
            role=None,
            content=None,
            chat_id=chat_id,
            is_complete=True,
            complete_reason=reason,
            is_error=False,
            error_message=None,
        )


CHAT_REQUEST = IncomingMessageConfiguration(
    CHAT_COMPLETION_REQUEST_METHOD, ChatCompletionRequestParams
)
