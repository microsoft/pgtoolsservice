# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import configparser

from ossdbtoolsservice.hosting.web_message_server import WebMessageServer

from ossdbtoolsservice.main import create_server_init, get_config, get_loggers, main
from ossdbtoolsservice.utils.async_runner import AsyncRunner


def _create_web_server(
    async_runner,
    server_logger,
    listen_address,
    listen_port,
    disable_keep_alive,
    debug_web_server,
    enable_dynamic_cors,
    config: configparser.ConfigParser,
):
    # Create the server, but don't start it yet
    server = WebMessageServer(
        async_runner=async_runner,
        logger=server_logger,
        listen_address=listen_address,
        listen_port=listen_port,
        disable_keep_alive=disable_keep_alive,
        debug_web_server=debug_web_server,
        enable_dynamic_cors=enable_dynamic_cors,
        config=config,
    )
    return create_server_init(server, server_logger)


if __name__ == "__main__":
    args, config = get_config()
    logger = get_loggers(args.log_dir)
    async_runner = AsyncRunner()
    server = _create_web_server(
        async_runner,
        logger,
        listen_address=args.listen_address,
        listen_port=args.listen_port,
        disable_keep_alive=args.disable_keep_alive,
        debug_web_server=args.debug_web_server,
        enable_dynamic_cors=args.enable_dynamic_cors,
        config=config,
    )

    try:
        main(server, args, logger)
    finally:
        async_runner.shutdown()
