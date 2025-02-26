# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import io
import json
from abc import ABC, abstractmethod
from logging import Logger

from ossdbtoolsservice.hosting.json_message import JSONRPCMessage


class JSONRPCWriter(ABC):
    """
    Abstract base class for writing JSON RPC messages
    """

    @abstractmethod
    def close(self) -> None:
        """
        Closes the writer
        """
        pass

    @abstractmethod
    def send_message(self, message: JSONRPCMessage) -> None:
        """
        Sends JSON RPC message as defined by message object
        :param message: Message to send
        """
        pass


class StreamJSONRPCWriter(JSONRPCWriter):
    """
    Write JSON RPC messages to a stream
    """

    HEADER = "Content-Length: {}\r\n\r\n"

    def __init__(
        self,
        stream: io.FileIO | io.BytesIO,
        encoding: str | None = None,
        logger: Logger | None = None,
    ) -> None:
        """
        Initializes the JSON RPC writer
        :param stream: Stream that messages will be sent on
        :param encoding: Optional encoding choice for messages. Defaults to UTF-8
        :param logger: Optional destination for logging
        """
        self.stream = stream
        self.encoding = encoding or "UTF-8"
        self._logger = logger

    # METHODS ##############################################################
    def close(self) -> None:
        """
        Closes the stream
        """
        try:
            self.stream.close()
        except Exception as e:
            if self._logger is not None:
                self._logger.exception(f"Exception raised when writer stream closed: {e}")

    def send_message(self, message: JSONRPCMessage) -> None:
        """
        Sends JSON RPC message as defined by message object
        :param message: Message to send
        """
        try:
            # Generate the message string and header string
            json_content = json.dumps(message.dictionary, sort_keys=True)
            header = self.HEADER.format(str(len(json_content)))

            # Write the message to the stream
            self.stream.write(header.encode("ascii"))
            self.stream.write(json_content.encode(self.encoding))
            self.stream.flush()

            if self._logger is not None:
                self._logger.info(
                    f"{message.message_type.name} message sent "
                    f"id={message.message_id} "
                    f"method={message.message_method} "
                    f"{json_content}"
                )

            # Uncomment for verbose logging
            # if self._logger:
            #     self._logger.info(f'{json_content}')

        except Exception as e:
            if self._logger is not None:
                self._logger.exception(
                    "Exception raised when sending message: "
                    f"{message.message_type} "
                    f"{message.message_id} "
                    f"{message.message_method} "
                    f"{e}"
                )
