from logging import Logger
from queue import Queue

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage
from ossdbtoolsservice.hosting.json_reader import JSONRPCReader
from ossdbtoolsservice.hosting.json_writer import JSONRPCWriter
from ossdbtoolsservice.hosting.rpc_message_server import RPCMessageServer
from ossdbtoolsservice.hosting.service_provider import Service, ServiceProvider
from ossdbtoolsservice.utils.async_runner import AsyncRunner


class QueueJSONRPCWriter(JSONRPCWriter):
    def __init__(self, queue: Queue[JSONRPCMessage]) -> None:
        self.queue = queue

    def close(self) -> None:
        pass

    def send_message(self, message: JSONRPCMessage) -> None:
        # Ensure serialized params
        JSONRPCMessage.from_dictionary(message.dictionary)
        self.queue.put(message)


class QueueJSONRPCReader(JSONRPCReader):
    def __init__(self, queue: Queue[JSONRPCMessage]) -> None:
        self.queue = queue

    def close(self) -> None:
        pass

    def read_message(self) -> JSONRPCMessage:
        return self.queue.get()


class QueueRPCMessageServer(RPCMessageServer):
    """Message server that uses a queue for input and output.

    Used for testing. Use with RPCMessageClientWrapper.
    """

    def __init__(
        self,
        input_queue: Queue[JSONRPCMessage] | None = None,
        output_queue: Queue[JSONRPCMessage] | None = None,
        async_runner: AsyncRunner | None = None,
        logger: Logger | None = None,
    ) -> None:
        self.input_queue = input_queue or Queue()
        self.output_queue = output_queue or Queue()
        super().__init__(
            QueueJSONRPCReader(self.input_queue),
            QueueJSONRPCWriter(self.output_queue),
            async_runner,
            logger,
        )
        self.service_provider: ServiceProvider | None = None

    def add_services(self, services: dict[str, type[Service] | Service]) -> None:
        if self.service_provider is not None:
            raise RuntimeError(
                "Service provider has already been initialized. "
                "Add all required services at start of test."
            )
        self.service_provider = ServiceProvider(self, services)
        self.service_provider.initialize()
