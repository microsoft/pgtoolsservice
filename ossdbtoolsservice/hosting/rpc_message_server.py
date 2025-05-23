import io
import threading
from logging import Logger
from queue import Queue

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage
from ossdbtoolsservice.hosting.json_reader import JSONRPCReader, StreamJSONRPCReader
from ossdbtoolsservice.hosting.json_writer import JSONRPCWriter, StreamJSONRPCWriter
from ossdbtoolsservice.hosting.message_recorder import MessageRecorder
from ossdbtoolsservice.hosting.message_server import MessageServer
from ossdbtoolsservice.utils.async_runner import AsyncRunner


class RPCMessageServer(MessageServer):
    def __init__(
        self,
        reader: JSONRPCReader,
        writer: JSONRPCWriter,
        async_runner: AsyncRunner | None,
        logger: Logger | None,
        version: str = "1",
        message_recorder: MessageRecorder | None = None,
    ) -> None:
        super().__init__(async_runner, logger, version, message_recorder)
        self.reader = reader
        self.writer = writer
        self._output_queue = Queue[JSONRPCMessage | None]()
        self._input_thread = threading.Thread(
            target=self._consume_input, name="JSONRPC_Input_Thread", daemon=True
        )
        self._output_thread = threading.Thread(
            target=self._consume_output, name="JSONRPC_Output_Thread", daemon=True
        )

    def start(self) -> None:
        self._log_info("Starting JSONRPC message server.")
        self._input_thread.start()
        self._output_thread.start()
        print("JSON RPC server started with input and output stream processing.")

    def stop(self) -> None:
        self._stop_requested = True
        self._log_info("Stopping JSONRPC message server.")
        # Unblock the output thread
        self._output_queue.put(None)

    def wait_for_exit(self) -> None:
        """
        Blocks until both input and output threads return, ie, until the server stops.
        """
        self._input_thread.join()
        self._output_thread.join()

        self._log_info("Input and output threads have completed")

        # Close the reader/writer here instead of in the stop method
        # in order to allow "softer"
        # shutdowns that will read or write the last message before halting
        self.reader.close()
        self.writer.close()

    def _send_message(self, message: JSONRPCMessage) -> None:
        self._output_queue.put(message)

    def _consume_input(self) -> None:
        self._log_info("JSONRPC input thread started.")
        while not self._stop_requested:
            try:
                message = self.reader.read_message()
                self._dispatch_message(message)
            except Exception as e:
                self._log_exception(f"Input thread exception: {e}")
                break

    def _consume_output(self) -> None:
        self._log_info("JSONRPC output thread started.")
        while not self._stop_requested:
            message = self._output_queue.get()
            if message is None:
                break
            try:
                self.writer.send_message(message)
            except Exception as e:
                self._log_exception(f"Output thread exception: {e}")


class StreamRPCMessageServer(RPCMessageServer):
    def __init__(
        self,
        in_stream: io.FileIO | io.BytesIO,
        out_stream: io.FileIO | io.BytesIO,
        async_runner: AsyncRunner | None,
        logger: Logger,
        version: str = "1",
        message_recorder: MessageRecorder | None = None,
    ) -> None:
        reader = StreamJSONRPCReader(in_stream, logger=logger)
        writer = StreamJSONRPCWriter(out_stream, logger=logger)

        super().__init__(
            reader,
            writer,
            async_runner,
            logger,
            version=version,
            message_recorder=message_recorder,
        )
