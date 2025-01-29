# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from dataclasses import dataclass
from ossdbtoolsservice.serialization import Serializable
from ossdbtoolsservice.hosting import (
    IncomingMessageConfiguration,
    OutgoingMessageRegistration,
)


@dataclass
class ChatMessageContent(Serializable):
    content: str | None = None
    participant: str | None = None


@dataclass
class ChatCompletionRequestParams(Serializable):
    owner_uri: str | None = None
    prompt: str | None = None
    document: str | None = None
    history: list[ChatMessageContent] | None = None


@dataclass
class CompletionResponse(Serializable):
    owner_uri: str | None = None
    prompt: str | None = None
    history: list[str] | None = None


@dataclass
class ChatCompletionResult(Serializable):
    content: str | None = None
    chat_id: str | None = None


CHAT_REQUEST = IncomingMessageConfiguration(
    "chat/completion-request", ChatCompletionRequestParams
)
CHAT_RESPONSE = OutgoingMessageRegistration.register_outgoing_message(
    CompletionResponse
)
