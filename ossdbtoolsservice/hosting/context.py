from abc import ABC, abstractmethod
from typing import Any


class RequestContext(ABC):
    """
    Abstract base class for a request context.
    Implementations will provide the logic to send responses, errors and notifications.
    """

    @abstractmethod
    def send_response(self, params: Any) -> None:
        pass

    @abstractmethod
    def send_error(self, message: str, data: Any = None, code: int = 0) -> None:
        pass

    @abstractmethod
    def send_notification(self, method: str, params: Any) -> None:
        pass


class NotificationContext(ABC):
    """
    Abstract base class for a notification context.
    """

    @abstractmethod
    def send_notification(self, method: str, params: Any) -> None:
        pass
