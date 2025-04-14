import logging
from typing import Any

from evaluations.chat_service_wrapper import (
    ChatCompletionError,
    ChatServiceResponse,
    ChatServiceWrapper,
)
from evaluations.settings import EvaluationSettings
from ossdbtoolsservice.chat.messages import ChatCompletionRequestParams, ChatMessageContent

logger = logging.getLogger(__name__)


class CompletionClientConnectionManager:
    """Context manager to handle connection to the chat service."""

    def __init__(self, completion_client: "CompletionClient"):
        self._completion_client = completion_client

    def __enter__(self) -> "CompletionClient":
        return self._completion_client

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        self._completion_client.disconnect()


class CompletionClient:
    def __init__(
        self,
        chat_service_wrapper: ChatServiceWrapper,
        eval_settings: EvaluationSettings,
    ):
        self._chat_service_wrapper = chat_service_wrapper
        self._eval_settings = eval_settings
        self._db_name: str | None = None
        self._suite_name: str | None = None

    def connect(self, suite_name: str, db_name: str) -> CompletionClientConnectionManager:
        """Connect to the chat service."""
        if self._db_name is not None or self._suite_name is not None:
            raise RuntimeError("Already connected to a chat service.")
        self._db_name = db_name
        self._suite_name = suite_name
        self._chat_service_wrapper.connect(
            self._db_name, self._suite_name, self._eval_settings
        )
        return CompletionClientConnectionManager(self)

    def disconnect(self) -> None:
        """Disconnect from the chat service."""
        if self._db_name is None or self._suite_name is None:
            raise RuntimeError("Not connected; use connect to connect to a database first.")
        self._chat_service_wrapper.disconnect(self._suite_name)
        self._db_name = None
        self._suite_name = None

    def get_response(
        self, prompt: str, history: list[ChatMessageContent] | None = None
    ) -> ChatServiceResponse:
        """Get a response from the chat service."""
        if self._db_name is None or self._suite_name is None:
            raise RuntimeError("Not connected; use connect to connect to a database first.")

        completion_request = ChatCompletionRequestParams(
            prompt=prompt,
            history=history or [],
            owner_uri=self._suite_name,
            profile_name=self._db_name,
        )

        retry_count = 1
        response: ChatServiceResponse | None = None
        while retry_count <= 3:
            try:
                response = self._chat_service_wrapper.get_response(completion_request)
                break
            except ChatCompletionError as e:
                logger.exception(e)
                if "RateLimitError" in str(e):
                    print(f"Rate limit error: {e.error_content.error_message}")
                    retry_count += 1
                else:
                    raise

        if response is None:
            raise RuntimeError(
                f"Failed to get a response after {retry_count - 1} retries due to rate limit."
            )
        return response
