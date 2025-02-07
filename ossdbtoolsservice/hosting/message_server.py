from abc import ABC, abstractmethod

from typing import Any, Callable, Generic, Type, TypeVar

from pydantic import BaseModel

from ossdbtoolsservice.hosting.context import (
    RequestContext,
    NotificationContext,
)
from ossdbtoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from ossdbtoolsservice.hosting.message_configuration import IncomingMessageConfiguration
from ossdbtoolsservice.serialization.serializable import Serializable


# Generic type for parameters (BaseModel, Serializable or a plain dict)
TModel = TypeVar("TModel", bound=BaseModel | Serializable | dict[str, Any])


###############################################################################
# Handler wrapper (for both requests and notifications)
###############################################################################


class MessageHandler(Generic[TModel]):
    def __init__(self, param_class: Type[Any], handler: Callable[[Any, TModel], None]):
        self.param_class = param_class
        self.handler = handler

    def deserialize_params(self, params: dict[str, Any]) -> Any:
        if self.param_class is None:
            # No complex deserialization
            return params

        if issubclass(self.param_class, BaseModel):
            return self.param_class.model_validate(params)

        if issubclass(self.param_class, Serializable):
            return self.param_class.from_dict(params)

        raise ValueError(f"Unsupported type for deserialization: {self.param_class}")


###############################################################################
# Common Base for Message Servers
###############################################################################


class MessageServer(ABC):
    """
    Common abstract base for both JSONRPC and Web message servers.
    Contains shared logic (e.g. registering handlers and dispatching messages).
    """

    def __init__(self, logger, version: str = "1"):
        self._logger = logger
        self._version = version
        self._stop_requested = False
        self._shutdown_handlers = []
        self._request_handlers: dict[str, MessageHandler] = {}
        self._notification_handlers: dict[str, MessageHandler] = {}

    def add_shutdown_handler(self, handler: Callable) -> None:
        self._shutdown_handlers.append(handler)

    def count_shutdown_handlers(self) -> int:
        return len(self._shutdown_handlers)

    def set_request_handler(
        self,
        config: IncomingMessageConfiguration[TModel],
        handler: Callable[[RequestContext, TModel], None],
    ) -> None:
        self._request_handlers[config.method] = MessageHandler(config.parameter_class, handler)

    def set_notification_handler(
        self,
        config: IncomingMessageConfiguration[TModel],
        handler: Callable[[NotificationContext, TModel], None],
    ) -> None:
        self._notification_handlers[config.method] = MessageHandler(
            config.parameter_class, handler
        )

    def _dispatch_message(self, message: JSONRPCMessage, **kwargs: Any) -> None:
        """Dispatches a message to the appropriate handler.

        This method is called by the input thread to process incoming messages.

        Args:
            message: The JSONRPCMessage to dispatch
            **kwargs: Additional arguments to pass to the
                create_request_context and create_notification_context methods
        """
        # Responses (success/error) are not handled here.
        if message.message_type in [
            JSONRPCMessageType.ResponseSuccess,
            JSONRPCMessageType.ResponseError,
        ]:
            return

        if message.message_type == JSONRPCMessageType.Request:
            self._log_info(
                f"Received request id={message.message_id} method={message.message_method}"
            )
            handler = self._request_handlers.get(message.message_method)
            context = self.create_request_context(message, **kwargs)
            if handler is None:
                context.send_error(
                    f"Requested method is unsupported: {message.message_method}"
                )
                self._log_warning(f"Unsupported method: {message.message_method}")
                return
            deserialized = handler.deserialize_params(message.message_params)
            try:
                handler.handler(context, deserialized)
            except Exception as e:
                error_msg = (
                    f"Unhandled exception for method {message.message_method}: {e}"
                )
                self._log_exception(error_msg)
                context.send_error(error_msg, code=-32603)
        elif message.message_type == JSONRPCMessageType.Notification:
            self._log_info(f"Received notification method={message.message_method}")
            handler = self._notification_handlers.get(message.message_method)
            context = self.create_notification_context(**kwargs)
            if handler is None:
                self._log_warning(
                    f"Notification method {message.message_method} is unsupported"
                )
                return
            deserialized = handler.deserialize_params(message.message_params)
            try:
                handler.handler(context, deserialized)
            except Exception as e:
                error_msg = f"Unhandled exception for notification {message.message_method}: {e}"
                self._log_exception(error_msg)
        else:
            self._log_warning(
                f"Received unsupported message type {message.message_type}"
            )

    def wait_for_exit(self) -> None:
        pass

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def send_request(self, method: str, params: Any) -> None:
        pass

    @abstractmethod
    def send_notification(self, method: str, params: Any) -> None:
        pass

    @abstractmethod
    def create_request_context(
        self, message: JSONRPCMessage, **kwargs: Any
    ) -> RequestContext:
        pass

    @abstractmethod
    def create_notification_context(self, **kwargs: Any) -> NotificationContext:
        pass

    def _log_exception(self, message: str) -> None:
        if self._logger is not None:
            self._logger.exception(message)

    def _log_warning(self, message: str) -> None:
        if self._logger is not None:
            self._logger.warning(message)

    def _log_info(self, message: str) -> None:
        if self._logger is not None:
            self._logger.info(message)
