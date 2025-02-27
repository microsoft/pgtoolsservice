# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
from typing import TYPE_CHECKING, Any

from ossdbtoolsservice.utils import serialization

if TYPE_CHECKING:
    from ossdbtoolsservice.hosting.lsp_message import LSPAny


class JSONRPCMessageType(Enum):
    Request = 1
    ResponseSuccess = 2
    ResponseError = 3
    Notification = 4


class JSONRPCMessage:
    """
    Internal representation of a JSON RPC message.
    Provides logic for converting back and forth from dictionary
    """

    # CONSTRUCTORS #########################################################
    @classmethod
    def create_error(
        cls, msg_id: str | int, code: int, message: str, data: Any
    ) -> "JSONRPCMessage":
        error = {"code": code, "message": message, "data": data}
        return cls(JSONRPCMessageType.ResponseError, msg_id=msg_id, msg_error=error)

    @classmethod
    def create_notification(cls, method: str, params: Any) -> "JSONRPCMessage":
        return cls(JSONRPCMessageType.Notification, msg_method=method, msg_params=params)

    @classmethod
    def create_request(cls, msg_id: str | int, method: str, params: Any) -> "JSONRPCMessage":
        return cls(
            JSONRPCMessageType.Request, msg_id=msg_id, msg_method=method, msg_params=params
        )

    @classmethod
    def create_response(cls, msg_id: str | int, result: Any) -> "JSONRPCMessage":
        return cls(JSONRPCMessageType.ResponseSuccess, msg_id=msg_id, msg_result=result)

    @classmethod
    def from_dictionary(cls, msg_dict: dict[str, Any]) -> "JSONRPCMessage":
        """
        Decomposes a dictionary from a JSON RPC message into components with light validation
        :param msg_dict: Dictionary of components from deserializing a JSON RPC message
        :return: JsonRpcMessage that is setup as per the dictionary
        """
        # Read all the possible values in from the message dictionary
        # If the keys don't exist in the dict, then None is set, which is acceptable
        msg_id = msg_dict.get("id")
        msg_method = msg_dict.get("method")
        msg_params = msg_dict.get("params")
        msg_result = msg_dict.get("result")
        msg_error = msg_dict.get("error")

        if msg_id is None:
            # Messages that lack an id are notifications
            if msg_method is None:
                raise ValueError("Notification message is missing method")
            msg_type = JSONRPCMessageType.Notification

        else:
            # Check for invalid error/result combo
            if msg_result is not None and msg_error is not None:
                raise ValueError("Message cannot have both result and error fields defined")

            # Message has id, therefore it is a response or a request
            if msg_result is not None:
                # A result field indicates this is a successful response
                msg_type = JSONRPCMessageType.ResponseSuccess
            elif msg_error is not None:
                # An error field indicated this is a failure response
                msg_type = JSONRPCMessageType.ResponseError
            else:
                # Lack of a result or error field indicates a request message
                if msg_method is None:
                    raise ValueError("Request message is missing method")
                msg_type = JSONRPCMessageType.Request

        return cls(msg_type, msg_id, msg_method, msg_params, msg_result, msg_error)

    def __init__(
        self,
        msg_type: JSONRPCMessageType,
        msg_id: str | int | None = None,
        msg_method: str | None = None,
        msg_params: dict[str, Any] | None = None,
        msg_result: Any | None = None,
        msg_error: dict[str, Any] | None = None,
    ):
        self._message_type = msg_type
        self._message_id = msg_id
        self._message_method = msg_method
        self._message_params = msg_params
        self._message_result = msg_result
        self._message_error = msg_error

    # PROPERTIES ###########################################################
    @property
    def message_id(self) -> str | int | None:
        return self._message_id

    @property
    def message_method(self) -> str | None:
        return self._message_method

    @property
    def message_params(self) -> "LSPAny | None":
        return self._message_params

    @property
    def message_result(self) -> "LSPAny | None":
        return self._message_result

    @property
    def message_error(self) -> dict[str, Any] | None:
        return self._message_error

    @property
    def message_type(self) -> JSONRPCMessageType:
        return self._message_type

    @property
    def dictionary(self) -> dict[str, Any]:
        message_dict: dict[str, Any] = {"jsonrpc": "2.0"}

        if self._message_type is JSONRPCMessageType.Request:
            message_dict["method"] = self._message_method
            message_dict["params"] = serialization.convert_to_dict(self._message_params)
            message_dict["id"] = self._message_id
        elif self._message_type is JSONRPCMessageType.ResponseSuccess:
            message_dict["result"] = serialization.convert_to_dict(self._message_result)
            message_dict["id"] = self._message_id
        elif self._message_type is JSONRPCMessageType.Notification:
            message_dict["method"] = self._message_method
            message_dict["params"] = serialization.convert_to_dict(self._message_params)
        elif self._message_type is JSONRPCMessageType.ResponseError:
            message_dict["error"] = serialization.convert_to_dict(self._message_error)
            message_dict["id"] = self._message_id
        else:
            raise ValueError(f"Unknown message type: {self._message_type}")

        return message_dict
