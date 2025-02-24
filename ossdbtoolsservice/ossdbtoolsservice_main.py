# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import io
import sys
from logging import Logger

from ossdbtoolsservice.hosting import MessageServer
from ossdbtoolsservice.hosting.message_recorder import MessageRecorder
from ossdbtoolsservice.hosting.rpc_message_server import StreamRPCMessageServer
from ossdbtoolsservice.main import create_server_init, get_config, get_loggers, main
from ossdbtoolsservice.utils.async_runner import AsyncRunner


def _create_server(
    input_stream: io.FileIO,
    output_stream: io.FileIO,
    server_logger: Logger,
    async_runner: AsyncRunner,
    message_recorder: MessageRecorder | None,
) -> MessageServer:
    # Create the server, but don't start it yet
    rpc_server = StreamRPCMessageServer(
        input_stream,
        output_stream,
        async_runner,
        server_logger,
        message_recorder=message_recorder,
    )
    return create_server_init(rpc_server, server_logger)


if __name__ == "__main__":
    args, _ = get_config()

    logger = get_loggers(args.log_dir)

    # Handle input file for stdin
    if args.input:
        stdin = open(args.input, "rb", buffering=0)  # noqa: SIM115
    else:
        # Wrap standard in and out in io streams to add readinto support
        stdin = open(sys.stdin.fileno(), "rb", buffering=0, closefd=False)  # noqa: SIM115

    std_out_wrapped = open(sys.stdout.fileno(), "wb", buffering=0, closefd=False)  # noqa: SIM115

    async_runner = AsyncRunner()

    message_recorder: MessageRecorder | None = None
    if args.record_messages_to_file:
        autosave_interval = args.recorder_autosave_seconds
        message_recorder = MessageRecorder(
            args.record_messages_to_file, save_interval=autosave_interval, logger=logger
        )

    server = _create_server(stdin, std_out_wrapped, logger, async_runner, message_recorder)

    try:
        main(server, args, logger)
    finally:
        async_runner.shutdown()
