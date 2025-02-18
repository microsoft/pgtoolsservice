import uuid
from abc import ABC, abstractmethod
from logging import Logger
from typing import Any, Callable, Generic, TypeVar

from pydantic import BaseModel

from ossdbtoolsservice.hosting.context import (
    NotificationContext,
    RequestContext,
)
from ossdbtoolsservice.hosting.errors import ResponseError
from ossdbtoolsservice.hosting.json_message import JSONRPCMessage, JSONRPCMessageType
from ossdbtoolsservice.hosting.message_configuration import IncomingMessageConfiguration
from ossdbtoolsservice.hosting.response_queues import ResponseQueues, SyncResponseQueues
from ossdbtoolsservice.serialization.serializable import Serializable
from ossdbtoolsservice.utils.async_runner import AsyncRunner

# Generic type for parameters (BaseModel, Serializable or a plain dict)
TModel = TypeVar("TModel", bound=BaseModel | Serializable | dict[str, Any])
TResult = TypeVar("TResult", bound=BaseModel | str | dict[str, Any])


###############################################################################
# Handler wrapper (for both requests and notifications)
###############################################################################


class MessageHandler(Generic[TModel]):
    def __init__(self, param_class: type[Any] | None, handler: Callable[[Any, TModel], None]):
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

    def __init__(
        self,
        async_runner: AsyncRunner | None,
        logger: Logger | None,
        version: str = "1",
    ):
        self.async_runner = async_runner
        self._logger = logger
        self._version = version
        self._stop_requested = False
        self._shutdown_handlers = []
        self._request_handlers: dict[str, MessageHandler] = {}
        self._notification_handlers: dict[str, MessageHandler] = {}

        # Register built-in handlers
        # 1) Echo
        echo_config = IncomingMessageConfiguration("echo", None)
        self.set_request_handler(echo_config, self._handle_echo_request)

        # 2) Protocol version
        version_config = IncomingMessageConfiguration("version", None)
        self.set_request_handler(version_config, self._handle_version_request)

        # 3) Shutdown/exit
        shutdown_config = IncomingMessageConfiguration("shutdown", None)
        self.set_request_handler(shutdown_config, self._handle_shutdown_request)
        exit_config = IncomingMessageConfiguration("exit", None)
        self.set_request_handler(exit_config, self._handle_shutdown_request)

        self._response_queues: ResponseQueues | SyncResponseQueues
        if async_runner is not None:
            self._response_queues = ResponseQueues()
        else:  # Synchronous
            self._response_queues = SyncResponseQueues()

    def add_shutdown_handler(self, handler: Callable) -> None:
        self._shutdown_handlers.append(handler)

    def count_shutdown_handlers(self) -> int:
        return len(self._shutdown_handlers)

    def set_request_handler(
        self,
        config: IncomingMessageConfiguration[TModel],
        handler: Callable[[RequestContext, TModel], None],
    ) -> None:
        self._request_handlers[config.method] = MessageHandler(
            config.parameter_class, handler
        )

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
        if message.message_type in [
            JSONRPCMessageType.ResponseSuccess,
            JSONRPCMessageType.ResponseError,
        ]:
            if self.async_runner and isinstance(self._response_queues, ResponseQueues):
                response_queue = self._response_queues.get_queue(message.message_id)
                if response_queue is not None:
                    self._log_info(f"Received response id={message.message_id}")
                    self.async_runner.run(response_queue.put(message))
                else:
                    self._log_warning(
                        f"Received response for unknown request id={message.message_id}"
                    )
            else:
                response_queue = self._response_queues.get_queue(message.message_id)
                if response_queue is not None:
                    self._log_info(f"Received response id={message.message_id}")
                    response_queue.put(message)
                else:
                    self._log_warning(
                        f"Received response for unknown request id={message.message_id}"
                    )
        elif message.message_type == JSONRPCMessageType.Request:
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
                error_msg = f"Unhandled exception for method {message.message_method}: {e}"
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
                error_msg = (
                    f"Unhandled exception for notification {message.message_method}: {e}"
                )
                self._log_exception(error_msg)
        else:
            self._log_warning(f"Received unsupported message type {message.message_type}")

    # BUILT-IN HANDLERS ####################################################

    @staticmethod
    def _handle_echo_request(request_context: RequestContext, params: Any) -> None:
        request_context.send_response(params)

    def _handle_version_request(self, request_context: RequestContext, _) -> None:
        request_context.send_response(self._version)

    def _handle_shutdown_request(self, request_context: RequestContext, _) -> None:
        # Signal that the threads should stop
        self._log_info("Received shutdown request")
        self._stop_requested = True

        # Execute the shutdown request handlers
        for handler in self._shutdown_handlers:
            handler()

        self.stop()

    def _log_exception(self, message: str) -> None:
        if self._logger is not None:
            self._logger.exception(message)

    def _log_warning(self, message: str) -> None:
        if self._logger is not None:
            self._logger.warning(message)

    def _log_info(self, message: str) -> None:
        if self._logger is not None:
            self._logger.info(message)

    def wait_for_exit(self) -> None:  # noqa: B027
        """Blocks until the server stops.

        Default implementation does nothing.
        """
        pass

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def _send_message(self, message: JSONRPCMessage) -> None:
        pass

    async def send_request(
        self,
        method: str,
        params: Any,
        result_type: type[TResult] | None = None,
        timeout: float | None = None,
    ) -> TResult | None:
        """
        Sends a request to the server and waits for a response.
        Args:
            method: The method to call
            params: The parameters to pass to the method
            result_type: The type of the result (optional)
            timeout: The timeout for the request, in seconds (optional)
        Raises:
            TimeoutError: If the request times out
            ResponseError: If the response contains an error
        Returns:
            The result of the request
        """
        if not isinstance(self._response_queues, ResponseQueues):
            raise ValueError("send_request is not supported in synchronous mode")

        message_id = str(uuid.uuid4())
        message = JSONRPCMessage.create_request(message_id, method, params)
        _response_queue = self._response_queues.register_new_queue(message_id)
        try:
            self._log_info(f" -- Sending request id={message_id} method={method}")
            self._send_message(message)
            response: JSONRPCMessage = await _response_queue.get()
            if response.message_type == JSONRPCMessageType.ResponseError:
                raise ResponseError(response.message_error)

            result_encoded = response.message_result

            if result_type is not None and issubclass(result_type, BaseModel):
                return result_type.model_validate(result_encoded)

            # For str or dict, return as-is
            return result_encoded
        finally:
            self._response_queues.delete_queue(message_id)

    def send_response(self, message_id: str, params: Any) -> None:
        response = JSONRPCMessage.create_response(message_id, params)
        self._send_message(response)

    def send_error(
        self, message_id: str, message: str, data: Any = None, code: int = 0
    ) -> None:
        error = JSONRPCMessage.create_error(message_id, code, message, data)
        self._send_message(error)

    def send_notification(self, method: str, params: Any) -> None:
        message = JSONRPCMessage.create_notification(method, params)
        self._send_message(message)

    def create_request_context(
        self, message: JSONRPCMessage, **kwargs: Any
    ) -> RequestContext:
        return RequestContext(message.message_id, self)

    def create_notification_context(self, **kwargs: Any) -> NotificationContext:
        return NotificationContext(self)
