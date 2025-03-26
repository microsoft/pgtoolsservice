"""Pydantic models representing Language Server Protocol (LSP) messages.

Use JSONRPCMessage for now, though these may eventually replace it.
"""

from enum import Enum, IntEnum
from typing import Any, Literal, TypeVar, Union

from pydantic import BaseModel

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from ossdbtoolsservice.serialization.serializable import Serializable

TModel = TypeVar("TModel", bound=BaseModel | Serializable)

LSPAny = dict[str, Any] | list[Any] | int | float | bool


class LSPMessageType(Enum):
    Request = 1
    ResponseSuccess = 2
    ResponseError = 3
    Notification = 4


class LSPMessage(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"

    def to_jsonrpc_message(self) -> JSONRPCMessage:
        if isinstance(self, LSPRequestMessage):
            return JSONRPCMessage.create_request(
                msg_id=self.id, method=self.method, params=self.params
            )
        if isinstance(self, LSPResponseResultMessage):
            return JSONRPCMessage.create_response(msg_id=str(self.id), result=self.result)
        if isinstance(self, LSPResponseErrorMessage):
            return JSONRPCMessage.create_error(
                msg_id=str(self.id),
                code=self.error.code,
                message=self.error.message,
                data=self.error.data,
            )
        if isinstance(self, LSPNotificationMessage):
            return JSONRPCMessage.create_notification(method=self.method, params=self.params)
        raise ValueError("Invalid LSP message type")

    @classmethod
    def from_dict(
        cls, message_dict: dict[str, Any]
    ) -> Union[
        "LSPRequestMessage",
        "LSPResponseResultMessage",
        "LSPResponseErrorMessage",
        "LSPNotificationMessage",
    ]:
        return _LSPMessages.model_validate({"message": message_dict}).message

    @classmethod
    def from_jsonrpc_message(
        cls, message: JSONRPCMessage
    ) -> Union[
        "LSPRequestMessage",
        "LSPResponseResultMessage",
        "LSPResponseErrorMessage",
        "LSPNotificationMessage",
    ]:
        if message.dictionary is None:
            raise ValueError("Invalid JSON-RPC message")
        if message.message_type == JSONRPCMessageType.Request:
            return LSPRequestMessage.model_validate(message.dictionary)
        if message.message_type == JSONRPCMessageType.ResponseSuccess:
            return LSPResponseResultMessage.model_validate(message.dictionary)
        if message.message_type == JSONRPCMessageType.ResponseError:
            return LSPResponseErrorMessage.model_validate(message.dictionary)
        if message.message_type == JSONRPCMessageType.Notification:
            return LSPNotificationMessage.model_validate(message.dictionary)
        raise ValueError("Invalid JSON-RPC message type")


class LSPRequestMessage(LSPMessage):
    id: str | int

    # Method being evoked
    method: str

    # The method's params.
    params: LSPAny | None = None

    def get_params(self, cls: type[TModel]) -> TModel:
        if not isinstance(self.params, dict):
            raise ValueError("Params are not a dictionary.")
        if issubclass(cls, BaseModel):
            # mypy doesn't understand that TModel is a BaseModel
            return cls.model_validate(self.params)  # type: ignore
        if issubclass(cls, Serializable):
            # mypy doesn't understand that TModel is a Serializable
            return cls.from_dict(self.params)  # type: ignore
        raise ValueError("Invalid params type")

    @classmethod
    def create(
        cls,
        id: str,
        method: str,
        params: BaseModel | LSPAny | None = None,
    ) -> "LSPRequestMessage":
        return cls(
            id=id,
            method=method,
            params=_params_to_dict(params) if isinstance(params, BaseModel) else params,
        )

    @classmethod
    def from_jsonrpc_message(cls, message: JSONRPCMessage) -> "LSPRequestMessage":
        if message.dictionary is None:
            raise ValueError("Invalid JSON-RPC message")
        return cls.model_validate(message.dictionary)


class LSPResponseResultMessage(LSPMessage):
    """The result of the request, if successful"""

    id: str | int

    # The result of the request. Can be null to just indicate success.
    result: LSPAny | None = None

    @classmethod
    def create(
        cls,
        id: str,
        result: Any | None = None,
    ) -> "LSPResponseResultMessage":
        return cls(id=id, result=result)

    @classmethod
    def from_jsonrpc_message(cls, message: JSONRPCMessage) -> "LSPResponseResultMessage":
        if message.dictionary is None:
            raise ValueError("Invalid JSON-RPC message")
        return cls.model_validate(message.dictionary)

    def get_result(self, cls: type[TModel]) -> TModel:
        if not isinstance(self.result, dict):
            raise ValueError("Result is not a dictionary.")
        if issubclass(cls, BaseModel):
            # mypy doesn't understand that TModel is a BaseModel
            return cls.model_validate(self.result)  # type: ignore
        if issubclass(cls, Serializable):
            # mypy doesn't understand that TModel is a Serializable
            return cls.from_dict(self.result)  # type: ignore
        raise ValueError("Invalid params type")


class ResponseError(BaseModel):
    message: str
    data: LSPAny | None = None

    # Error codes defined below.
    # union with int for custom error codes
    code: Union["LSPErrorCode", int]


class LSPResponseErrorMessage(LSPMessage):
    """The error of the request, if unsuccessful"""

    id: str | int

    error: ResponseError

    @classmethod
    def create(
        cls,
        id: str,
        error: ResponseError,
    ) -> "LSPResponseErrorMessage":
        return cls(id=id, error=error)

    @classmethod
    def from_jsonrpc_message(cls, message: JSONRPCMessage) -> "LSPResponseErrorMessage":
        if message.dictionary is None:
            raise ValueError("Invalid JSON-RPC message")
        return cls.model_validate(message.dictionary)


class LSPNotificationMessage(LSPMessage):
    # Method being evoked
    method: str

    # The method's params. Only support Object params.
    params: LSPAny | None = None

    def get_params(self, cls: type[TModel]) -> TModel:
        if not isinstance(self.params, dict):
            raise ValueError("Params are not a dictionary.")
        if issubclass(cls, BaseModel):
            # mypy doesn't understand that TModel is a BaseModel
            return cls.model_validate(self.params)  # type: ignore
        if issubclass(cls, Serializable):
            # mypy doesn't understand that TModel is a Serializable
            return cls.from_dict(self.params)  # type: ignore
        raise ValueError("Invalid params type")

    @classmethod
    def create(
        cls,
        method: str,
        params: BaseModel | None = None,
    ) -> "LSPNotificationMessage":
        return cls(method=method, params=_params_to_dict(params))

    @classmethod
    def from_jsonrpc_message(cls, message: JSONRPCMessage) -> "LSPNotificationMessage":
        if message.dictionary is None:
            raise ValueError("Invalid JSON-RPC message")
        return cls.model_validate(message.dictionary)


class _LSPMessages(BaseModel):
    """Internal model class used to deserialize LSP messages"""

    message: (
        LSPRequestMessage
        | LSPResponseResultMessage
        | LSPResponseErrorMessage
        | LSPNotificationMessage
    )


class LSPErrorCode(IntEnum):
    # Defined by JSON-RPC
    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603

    # This is the start range of JSON-RPC reserved error codes.
    # It doesn't denote a real error code. No LSP error codes should
    # be defined between the start and end range. For backwards
    # compatibility the `ServerNotInitialized` and the `UnknownErrorCode`
    # are left in the range.
    #
    # @since 3.16.0
    jsonrpcReservedErrorRangeStart = -32099
    # @deprecated use jsonrpcReservedErrorRangeStart
    serverErrorStart = jsonrpcReservedErrorRangeStart

    # Error code indicating that a server received a notification or
    # request before the server has received the `initialize` request.
    ServerNotInitialized = -32002
    UnknownErrorCode = -32001

    # This is the end range of JSON-RPC reserved error codes.
    # It doesn't denote a real error code.
    #
    # @since 3.16.0
    jsonrpcReservedErrorRangeEnd = -32000
    # @deprecated use jsonrpcReservedErrorRangeEnd
    serverErrorEnd = jsonrpcReservedErrorRangeEnd

    # This is the start range of LSP reserved error codes.
    # It doesn't denote a real error code.
    #
    # @since 3.16.0
    lspReservedErrorRangeStart = -32899

    # A request failed but it was syntactically correct, e.g the
    # method name was known and the parameters were valid. The error
    # message should contain human readable information about why
    # the request failed.
    #
    # @since 3.17.0
    RequestFailed = -32803

    # The server cancelled the request. This error code should
    # only be used for requests that explicitly support being
    # server cancellable.
    #
    # @since 3.17.0
    ServerCancelled = -32802

    # The server detected that the content of a document got
    # modified outside normal conditions. A server should
    # NOT send this error code if it detects a content change
    # in it unprocessed messages. The result even computed
    # on an older state might still be useful for the client.
    #
    # If a client decides that a result is not of any use anymore
    # the client should cancel the request.
    ContentModified = -32801

    # The client has canceled a request and a server has detected
    # the cancel.
    RequestCancelled = -32800

    # This is the end range of LSP reserved error codes.
    # It doesn't denote a real error code.
    #
    # @since 3.16.0
    lspReservedErrorRangeEnd = -32800


def _params_to_dict(params: BaseModel | None) -> dict[str, Any] | None:
    return (
        params.model_dump(
            mode="json", exclude_none=False, exclude_defaults=False, by_alias=True
        )
        if params
        else None
    )
