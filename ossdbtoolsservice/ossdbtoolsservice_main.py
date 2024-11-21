# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import io
import logging
import os
import sys
import debugpy

from ossdbtoolsservice.admin import AdminService
from ossdbtoolsservice.capabilities.capabilities_service import CapabilitiesService
from ossdbtoolsservice.connection import ConnectionService
from ossdbtoolsservice.disaster_recovery.disaster_recovery_service import DisasterRecoveryService
from ossdbtoolsservice.hosting import JSONRPCServer, ServiceProvider
from ossdbtoolsservice.language import LanguageService
from ossdbtoolsservice.metadata import MetadataService
from ossdbtoolsservice.object_explorer import ObjectExplorerService
from ossdbtoolsservice.query_execution import QueryExecutionService
from ossdbtoolsservice.scripting.scripting_service import ScriptingService
from ossdbtoolsservice.edit_data.edit_data_service import EditDataService
from ossdbtoolsservice.tasks import TaskService
from ossdbtoolsservice.utils import constants, markdown
from ossdbtoolsservice.workspace import WorkspaceService

def _create_server(input_stream, output_stream, server_logger, provider):
    # Create the server, but don't start it yet
    rpc_server = JSONRPCServer(input_stream, output_stream, server_logger)
    return _create_server_init(rpc_server, provider, server_logger)

def _create_web_server(server_logger, provider, listen_address, listen_port, disable_keep_alive, debug_web_server):
    # Create the server, but don't start it yet
    rpc_server = JSONRPCServer(logger=server_logger, enable_web_server=True, listen_address=listen_address, listen_port=listen_port, disable_keep_alive=disable_keep_alive, debug_web_server=debug_web_server)
    return _create_server_init(rpc_server, provider, server_logger)

def _create_server_init(rpc_server, provider, server_logger):
    # Create the service provider and add the providers to it
    services = {
        constants.ADMIN_SERVICE_NAME: AdminService,
        constants.CAPABILITIES_SERVICE_NAME: CapabilitiesService,
        constants.CONNECTION_SERVICE_NAME: ConnectionService,
        constants.DISASTER_RECOVERY_SERVICE_NAME: DisasterRecoveryService,
        constants.LANGUAGE_SERVICE_NAME: LanguageService,
        constants.METADATA_SERVICE_NAME: MetadataService,
        constants.OBJECT_EXPLORER_NAME: ObjectExplorerService,
        constants.QUERY_EXECUTION_SERVICE_NAME: QueryExecutionService,
        constants.SCRIPTING_SERVICE_NAME: ScriptingService,
        constants.WORKSPACE_SERVICE_NAME: WorkspaceService,
        constants.EDIT_DATA_SERVICE_NAME: EditDataService,
        constants.TASK_SERVICE_NAME: TaskService
    }
    service_box = ServiceProvider(rpc_server, services, provider, server_logger)
    service_box.initialize()
    return rpc_server

if __name__ == '__main__':
    # See if we have any arguments
    wait_for_debugger = False
    log_dir = None
    stdin = None
    # Setting a default provider name to test PG extension
    provider_name = constants.PG_PROVIDER_NAME

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Start the Tools Service')
    parser.add_argument('--generate-markdown', action='store_true', help='Generate Markdown documentation for requests')
    parser.add_argument('--input', type=str, help='Input file for stdin')
    parser.add_argument('--enable-web-server', action='store_true', help='Enable the web server to receive requests over HTTP and WebSocket')
    parser.add_argument('--listen-address', type=str, default='0.0.0.0', help='Address to listen on for the web server (default:0.0.0.0)')
    parser.add_argument('--listen-port', type=int, default=80, help='Port to listen on for the web server (default:80)')
    parser.add_argument('--debug-web-server', action='store_true', help='Enable debug mode for the web server')
    parser.add_argument('--disable-keep-alive', action='store_true', help='Disable keep-alive for the web server. Should not be used in production only for debugging')
    parser.add_argument('--enable-remote-debugging', type=int, nargs='?', const=3000, help='Enable remote debugging on the specified port (default: 3000)')
    parser.add_argument('--enable-remote-debugging-wait', type=int, nargs='?', const=3000, help='Enable remote debugging and wait for the debugger to attach on the specified port (default: 3000)')
    parser.add_argument('--log-dir', type=str, help='Directory to store logs')
    parser.add_argument('--provider', type=str, help='Provider name')
    args = parser.parse_args()

    # Handle input file for stdin
    if args.input:
        stdin = io.open(args.input, 'rb', buffering=0)

    # Handle remote debugging
    if args.enable_remote_debugging or args.enable_remote_debugging_wait:
        port = args.enable_remote_debugging or args.enable_remote_debugging_wait
        try:
            os.environ["DEBUGPY_LOG_DIR"] = "./debugpy_logs"  # Path to store logs
            # Dynamically set the Python interpreter for debugpy fron an environment variable or default to the current interpreter.
            python_path = os.getenv("PYTHON", default=sys.executable)
            debugpy.configure(python=python_path)
            debugpy.listen(("127.0.0.1", port))
        except BaseException:
            # If port 3000 is used, try another debug port
            port += 1
            debugpy.listen(("127.0.0.1", port))
        if args.enable_remote_debugging_wait:
            wait_for_debugger = True

    # Handle log directory
    log_dir = args.log_dir if args.log_dir else os.path.dirname(sys.argv[0])

    # Handle provider name
    if args.provider:
        provider_name = args.provider
        # Check if we support the given provider
        supported = provider_name in constants.SUPPORTED_PROVIDERS
        if not supported:
            raise AssertionError("{} is not a supported provider".format(str(provider_name)))

    # Create the output logger
    logger = logging.getLogger('ossdbtoolsservice')
    try:
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(os.path.join(log_dir, 'ossdbtoolsservice.log'))
    except Exception:
        handler = logging.NullHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    # Wait for the debugger to attach if needed
    if wait_for_debugger:
        logger.debug('Waiting for a debugger to attach...')
        debugpy.wait_for_client()

    # Wrap standard in and out in io streams to add readinto support
    if stdin is None:
        stdin = io.open(sys.stdin.fileno(), 'rb', buffering=0, closefd=False)

    std_out_wrapped = io.open(sys.stdout.fileno(), 'wb', buffering=0, closefd=False)

    logger.info('{0} Tools Service is starting up...'.format(provider_name))

    # Create the server, but don't start it yet
    server=None
    if args.enable_web_server:
        server = _create_web_server(logger, provider_name, listen_address=args.listen_address, listen_port=args.listen_port, disable_keep_alive=args.disable_keep_alive, debug_web_server=args.debug_web_server)
    else:
        server = _create_server(stdin, std_out_wrapped, logger, provider_name)

    # Generate Markdown if the feature switch is enabled
    if args.generate_markdown:
        markdown.generate_requests_markdown(server, logger)
    else:
        # Start the server
        server.start()
        server.wait_for_exit()
