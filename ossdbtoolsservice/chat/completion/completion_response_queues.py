import uuid
from asyncio import Queue

from .messages import (
    VSCodeLanguageModelChatCompletionResponse,
    VSCodeLanguageModelCompleteResultPart,
    VSCodeLanguageModelTextPart,
    VSCodeLanguageModelToolCallPart,
)

ResponsePart = (
    VSCodeLanguageModelCompleteResultPart
    | VSCodeLanguageModelTextPart
    | VSCodeLanguageModelToolCallPart
)


class CompletionResponseQueues:
    def __init__(self) -> None:
        self._queues: dict[str, Queue[ResponsePart]] = {}

    def register_new_queue(self) -> tuple[str, Queue[ResponsePart]]:
        request_id = str(uuid.uuid4())
        queue = Queue[ResponsePart]()
        self._queues[request_id] = queue
        return request_id, queue

    def get_queue(self, request_id: str) -> Queue[ResponsePart]:
        return self._queues[request_id]

    def delete_queue(self, request_id: str) -> None:
        del self._queues[request_id]

    async def handle_completion_response(
        self, message: VSCodeLanguageModelChatCompletionResponse
    ) -> None:
        queue = self.get_queue(message.request_id)
        await queue.put(message.response)
