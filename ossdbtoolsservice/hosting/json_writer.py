# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json


class JSONRPCWriter:
    """
    Write JSON RPC messages to a stream
    """

    HEADER = u"Content-Length: {}\r\n\r\n"

    def __init__(self, stream, encoding=None, logger=None):
        """
        Initializes the JSON RPC writer
        :param stream: Stream that messages will be sent on
        :param encoding: Optional encoding choice for messages. Defaults to UTF-8
        :param logger: Optional destination for logging
        """
        self.stream = stream
        self.encoding = encoding or 'UTF-8'
        self._logger = logger

    # METHODS ##############################################################
    def close(self):
        """
        Closes the stream
        """
        try:
            self.stream.close()
        except Exception as e:
            if self._logger is not None:
                self._logger.exception(f'Exception raised when writer stream closed: {e}')

    def send_message(self, message):
        """
        Sends JSON RPC message as defined by message object
        :param message: Message to send
        """
        # Generate the message string and header string
        json_content = json.dumps(message.dictionary, sort_keys=True)
        header = self.HEADER.format(str(len(json_content)))

        # Write the message to the stream
        self.stream.write(header.encode(u"ascii"))
        self.stream.write(json_content.encode(self.encoding))
        self.stream.flush()

        if self._logger is not None:
            self._logger.info("{} message sent id={} method={}".format(
                message.message_type.name,
                message.message_id,
                message.message_method
            ))

            # Uncomment for verbose logging
            # self._logger.debug(f'{json_content}')
