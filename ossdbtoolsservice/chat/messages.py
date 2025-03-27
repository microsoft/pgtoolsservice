# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum

from ossdbtoolsservice.az.models import AzureToken
from ossdbtoolsservice.core.models import PGTSBaseModel
from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
)
from ossdbtoolsservice.query.contracts.result_set_summary import ResultSetSummary
from ossdbtoolsservice.query.contracts.selection_data import SelectionData
from ossdbtoolsservice.query_execution.contracts.message_notification import ResultMessage

# Requests
CHAT_COMPLETION_REQUEST_METHOD = "chat/completion-request"

# Notifications
CHAT_FUNCTION_CALL_NOTIFICATION_METHOD = "chat/function-call-notification"
CHAT_FUNCTION_CALL_ERROR_NOTIFICATION_METHOD = "chat/function-call-error-notification"
CHAT_COMPLETION_RESULT_METHOD = "chat/completion-result"
COPILOT_QUERY_NOTIFICATION_METHOD = "chat/notify-copilot-query"


class CopilotAccessMode(str, Enum):
    READ_ONLY = "ro"
    READ_WRITE = "rw"

    def __str__(self) -> str:
        return self.value


class ChatMessageContent(PGTSBaseModel):
    participant: str
    content: str


class ChatCompletionRequestParams(PGTSBaseModel):
    prompt: str
    history: list[ChatMessageContent]
    owner_uri: str
    """The owner URI for the document or node that owns the database 
    connection that the completion request will use"""
    profile_name: str
    """The name of the profile to use for the completion request.
    
    This is the name of the server and database for the connection,
    as the user understands it."""

    session_id: str | None = None
    """The session ID for the completion request.
    
    The sessionId identifies the chat thread. It is used to cache
    tool calls and results in the history of the thread. If unset,
    no caching will occur.
    """

    active_editor_uri: str | None = None
    """The URI of the active editor, if any."""

    active_editor_selection: SelectionData | None = None
    """The selection in the active editor, if any."""

    result_set_summaries: list[ResultSetSummary] | None = None
    """The result set summaries, if the active editor has results"""

    result_messages: list[ResultMessage] | None = None
    """The result messages, if the active editor has results"""

    arm_token: AzureToken | None = None
    """Optional Azure token for interacting with Azure Resource Manager."""

    access_mode: CopilotAccessMode | None = None
    """The access mode for the completion request."""


class ChatCompletionRequestResult(PGTSBaseModel):
    """Result of a chat completion request.

    Notifies the client of the chat_id that will be used
    to identify completion content delivered through
    notifications.
    """

    chat_id: str


class ChatFunctionCallNotificationParams(PGTSBaseModel):
    chat_id: str
    function_name: str

    # ONLY arguments that will not contain user data.
    function_args: dict[str, str] | None = None

    message: str


class ChatFunctionCallErrorNotificationParams(PGTSBaseModel):
    chat_id: str
    function_name: str


class CopilotQueryNotificationParams(PGTSBaseModel):
    query_name: str
    query_description: str
    query: str
    owner_uri: str
    has_error: bool = False
    chat_id: str


class ChatCompletionContent(PGTSBaseModel):
    """Chat completion result part sent as a notification to the client."""

    role: str | None
    content: str | None = None
    chat_id: str
    is_complete: bool = False
    complete_reason: str | None = None
    is_error: bool = False
    error_message: str | None = None

    @classmethod
    def error(cls, chat_id: str, error_message: str) -> "ChatCompletionContent":
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
    def response_part(cls, chat_id: str, role: str, content: str) -> "ChatCompletionContent":
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
    def complete(cls, chat_id: str, reason: str) -> "ChatCompletionContent":
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
