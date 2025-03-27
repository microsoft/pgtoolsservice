from queue import Queue
from threading import Lock

from pydantic import BaseModel

from ossdbtoolsservice.chat.messages import (
    CHAT_COMPLETION_REQUEST_METHOD,
    CHAT_COMPLETION_RESULT_METHOD,
    COPILOT_QUERY_NOTIFICATION_METHOD,
    ChatCompletionContent,
    ChatCompletionRequestParams,
    ChatCompletionRequestResult,
    CopilotQueryNotificationParams,
)
from ossdbtoolsservice.hosting.lsp_message import LSPNotificationMessage
from tests_v2.test_utils.message_server_client_wrapper import MessageServerClientWrapper


class ChatCompletionError(Exception):
    def __init__(self, error_content: ChatCompletionContent) -> None:
        message = error_content.error_message
        super().__init__(message)
        self.error_content = error_content


class ChatServiceResponse(BaseModel):
    """Encapsulates the respone retrieved from the ChatServiceWrapper."""

    response: str
    queries_executed: list[str] = []


class ChatServiceWrapper:
    def __init__(self, server_client_wrapper: MessageServerClientWrapper):
        self._server_client_wrapper = server_client_wrapper

        self._server_client_wrapper.add_notification_handler(
            CHAT_COMPLETION_RESULT_METHOD, self._handle_notifications
        )

        self._server_client_wrapper.add_notification_handler(
            COPILOT_QUERY_NOTIFICATION_METHOD, self._handle_notifications
        )

        self._completion_queues: dict[
            str, Queue[ChatCompletionContent | CopilotQueryNotificationParams]
        ] = {}
        self._lock = Lock()

    def _handle_notifications(self, notification: LSPNotificationMessage) -> None:
        if notification.method == CHAT_COMPLETION_RESULT_METHOD:
            result_part = notification.get_params(ChatCompletionContent)
            chat_id = result_part.chat_id
            with self._lock:
                if chat_id not in self._completion_queues:
                    self._completion_queues[chat_id] = Queue()
            self._completion_queues[chat_id].put(result_part)
        elif notification.method == COPILOT_QUERY_NOTIFICATION_METHOD:
            query_notification = notification.get_params(CopilotQueryNotificationParams)
            with self._lock:
                if query_notification.chat_id not in self._completion_queues:
                    self._completion_queues[query_notification.chat_id] = Queue()
            self._completion_queues[query_notification.chat_id].put(query_notification)
        else:
            raise ValueError(f"Unknown notification method: {notification.method}")

    def get_response(self, request: ChatCompletionRequestParams) -> ChatServiceResponse:
        response = self._server_client_wrapper.send_client_request(
            method=CHAT_COMPLETION_REQUEST_METHOD, params=request, timeout=None
        )
        chat_id = response.get_result(ChatCompletionRequestResult).chat_id
        with self._lock:
            if chat_id not in self._completion_queues:
                self._completion_queues[chat_id] = Queue()
        queue = self._completion_queues[chat_id]
        response = ""
        queries_executed: list[str] = []
        while True:
            params = queue.get()
            if isinstance(params, CopilotQueryNotificationParams):
                queries_executed.append(params.query)
            else:
                result_part: ChatCompletionContent = params
                if result_part.is_error:
                    raise ChatCompletionError(result_part)
                if result_part.is_complete:
                    break
                if result_part.content:
                    response += result_part.content

        return ChatServiceResponse(
            response=response,
            queries_executed=queries_executed,
        )
