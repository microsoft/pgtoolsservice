from typing import TYPE_CHECKING, Any, Type

from ossdbtoolsservice.utils.async_runner import AsyncRunner

if TYPE_CHECKING:
    from ossdbtoolsservice.hosting.message_server import MessageServer, TResult


class HandlerContext:
    """
    Base class for a handler context.
    Implementations can provide their own logic to send responses, errors and notifications.
    """

    def __init__(self, server: "MessageServer") -> None:
        self.server = server

    def get_async_runner(self) -> AsyncRunner | None:
        return self.server.async_runner

    def send_notification(self, method: str, params: Any) -> None:
        self.server.send_notification(method, params)

    async def send_request(
        self,
        method: str,
        params: Any,
        result_type: Type["TResult"],
    ) -> "TResult | None":
        return await self.server.send_request(method, params, result_type)


class RequestContext(HandlerContext):
    """
    Base class for a request context.
    Implementations can provide their own logic to send responses, errors and notifications.
    """

    def __init__(self, message_id: str, server: "MessageServer") -> None:
        self.message_id = message_id
        super().__init__(server)

    def send_response(self, params: Any) -> None:
        self.server.send_response(self.message_id, params)

    def send_error(self, message: str, data: Any = None, code: int = 0) -> None:
        self.server.send_error(self.message_id, message, data, code)


class NotificationContext(HandlerContext):
    """
    Base class for a notification context.
    """

    pass
