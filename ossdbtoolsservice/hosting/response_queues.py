import asyncio
from queue import Queue as SyncQueue
from typing import Generic, TypeVar

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage

T = TypeVar("T")


class TimeoutQueue(Generic[T], asyncio.Queue[T]):
    async def get(self, timeout: float | None = None) -> T:
        """
        Get an item from the queue, with an optional timeout.

        :param timeout: The maximum number of seconds to wait for an item. If None, wait indefinitely.
        :return: The item from the queue.
        :raises asyncio.TimeoutError: If the timeout expires before an item is available.
        """
        if timeout is None:
            return await super().get()
        else:
            return await asyncio.wait_for(super().get(), timeout)

    async def put(self, item: T, timeout: float | None = None) -> None:
        """
        Put an item into the queue, with an optional timeout.

        :param timeout: The maximum number of seconds to wait to put the item. If None, wait indefinitely.
        :raises asyncio.TimeoutError: If the timeout expires before the item is put into the queue.
        """
        if timeout is None:
            await super().put(item)
        else:
            await asyncio.wait_for(super().put(item), timeout)


class ResponseQueues:
    def __init__(self) -> None:
        self._queues: dict[str, TimeoutQueue[JSONRPCMessage]] = {}

    def register_new_queue(self, request_id: str) -> TimeoutQueue[JSONRPCMessage]:
        queue = TimeoutQueue[JSONRPCMessage]()
        self._queues[request_id] = queue
        return queue

    def get_queue(self, request_id: str) -> TimeoutQueue[JSONRPCMessage] | None:
        return self._queues.get(request_id)

    def delete_queue(self, request_id: str) -> None:
        del self._queues[request_id]


class SyncResponseQueues:
    def __init__(self) -> None:
        self._queues: dict[str, SyncQueue[JSONRPCMessage]] = {}

    def register_new_queue(self, request_id: str) -> SyncQueue[JSONRPCMessage]:
        queue = SyncQueue[JSONRPCMessage]()
        self._queues[request_id] = queue
        return queue

    def get_queue(self, request_id: str) -> SyncQueue[JSONRPCMessage] | None:
        return self._queues.get(request_id)

    def delete_queue(self, request_id: str) -> None:
        if request_id in self._queues:
            del self._queues[request_id]
