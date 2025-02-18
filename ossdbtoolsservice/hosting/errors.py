from typing import Any


class ResponseError(Exception):
    def __init__(self, message_error: dict[str, Any]):
        message = message_error["message"]
        super().__init__(message)
        self.message = message
        self.message_error = message_error
