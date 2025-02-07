# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import io
import sys

from ossdbtoolsservice.hosting import MessageServer, ServiceProvider
from ossdbtoolsservice.hosting.rpc_message_server import RPCMessageServer
from ossdbtoolsservice.main import create_server_init, get_config, get_loggers, main
from ossdbtoolsservice.utils.async_runner import AsyncRunner


def _create_server(
    input_stream, output_stream, server_logger, provider
) -> tuple[MessageServer, ServiceProvider]:
    # Create the server, but don't start it yet
    rpc_server = RPCMessageServer(input_stream, output_stream, server_logger)
    async_runner = AsyncRunner()
    return create_server_init(
        rpc_server, provider, server_logger, async_runner=async_runner
    )


if __name__ == "__main__":
    args, _ = get_config()

    logger = get_loggers(args.log_dir)

    # Handle input file for stdin
    if args.input:
        stdin = io.open(args.input, "rb", buffering=0)
    else:
        # Wrap standard in and out in io streams to add readinto support    
        stdin = io.open(sys.stdin.fileno(), "rb", buffering=0, closefd=False)

    std_out_wrapped = io.open(sys.stdout.fileno(), "wb", buffering=0, closefd=False)

    server, service_box = _create_server(stdin, std_out_wrapped, logger, "PGSQL")

    main(server, service_box, args, logger)
