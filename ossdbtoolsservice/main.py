# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
import configparser
import logging
import os
import sys
from typing import Type

import debugpy

from ossdbtoolsservice.admin import AdminService
from ossdbtoolsservice.capabilities.capabilities_service import CapabilitiesService
from ossdbtoolsservice.chat.chat_service import ChatService
from ossdbtoolsservice.connection import ConnectionService
from ossdbtoolsservice.disaster_recovery.disaster_recovery_service import (
    DisasterRecoveryService,
)
from ossdbtoolsservice.edit_data.edit_data_service import EditDataService
from ossdbtoolsservice.hosting import MessageServer, Service, ServiceProvider
from ossdbtoolsservice.language import LanguageService
from ossdbtoolsservice.metadata import MetadataService
from ossdbtoolsservice.object_explorer import ObjectExplorerService
from ossdbtoolsservice.query_execution import QueryExecutionService
from ossdbtoolsservice.scripting.scripting_service import ScriptingService
from ossdbtoolsservice.tasks import TaskService
from ossdbtoolsservice.utils import constants, markdown
from ossdbtoolsservice.utils.bool import str_to_bool
from ossdbtoolsservice.utils.path import path_relative_to_base
from ossdbtoolsservice.workspace import WorkspaceService


def create_server_init(
    message_server: MessageServer,
    server_logger: logging.Logger | None,
) -> MessageServer:
    # Create the service provider and add the providers to it
    services: dict[str, Type[Service]] = {
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
        constants.TASK_SERVICE_NAME: TaskService,
        constants.CHAT_SERVICE_NAME: ChatService,
    }
    service_box = ServiceProvider(message_server, services, server_logger)
    service_box.initialize()
    return message_server


def get_config() -> tuple[argparse.Namespace, configparser.ConfigParser]:
    # Load configuration from the config file
    config = configparser.ConfigParser()
    config.read(path_relative_to_base("config.ini"))

    defaults = {
        "log_dir": config.get("general", "log_dir", fallback=os.path.dirname(sys.argv[0])),
        "enable_web_server": config.get("server", "enable_web_server", fallback="false"),
        "listen_address": config.get("server", "listen_address", fallback="0.0.0.0"),
        "listen_port": config.get("server", "listen_port", fallback="8443"),
        "console_logging": config.get("server", "console_logging", fallback="false"),
        "disable_keep_alive": config.get("server", "disable_keep_alive", fallback="false"),
        "enable_dynamic_cors": config.get("server", "enable_dynamic_cors", fallback="false"),
    }

    # Override config defaults with environment variables (if present)
    log_dir_env = os.getenv("LOG_DIR", defaults["log_dir"])
    enable_web_server_env = os.getenv("ENABLE_WEB_SERVER", defaults["enable_web_server"])
    listen_address_env = os.getenv("LISTEN_ADDRESS", defaults["listen_address"])
    listen_port_env = os.getenv("LISTEN_PORT", defaults["listen_port"])
    console_logging_env = os.getenv("CONSOLE_LOGGING", defaults["console_logging"])
    disable_keep_alive_env = os.getenv("DISABLE_KEEP_ALIVE", defaults["disable_keep_alive"])
    enable_dynamic_cors_env = os.getenv(
        "ENABLE_DYNAMIC_CORS", defaults["enable_dynamic_cors"]
    )

    # Parse command-line arguments (takes precidence over config file and environment variables)
    parser = argparse.ArgumentParser(description="Start the Tools Service")
    parser.add_argument(
        "--generate-markdown",
        action="store_true",
        help="Generate Markdown documentation for requests",
    )
    parser.add_argument("--input", type=str, help="Input file for stdin")
    parser.add_argument(
        "--enable-web-server",
        action="store_true",
        default=str_to_bool(enable_web_server_env),
        help="Enable the web server to receive requests over HTTP and WebSocket",
    )
    parser.add_argument(
        "--listen-address",
        type=str,
        default=listen_address_env,
        help="Address to listen on for the web server (default:0.0.0.0)",
    )
    parser.add_argument(
        "--listen-port",
        type=int,
        default=int(listen_port_env),
        help="Port to listen on for the web server (default:8443)",
    )
    parser.add_argument(
        "--debug-web-server",
        action="store_true",
        help="Enable debug mode for the web server",
    )
    parser.add_argument(
        "--disable-keep-alive",
        action="store_true",
        default=str_to_bool(disable_keep_alive_env),
        help="Disable keep-alive for the web server. Should not be used in production only for debugging",
    )
    parser.add_argument(
        "--enable-dynamic-cors",
        action="store_true",
        default=str_to_bool(enable_dynamic_cors_env),
        help="Enable dynamic setting of CORS, allow any origin. Should not be used in production only for debugging",
    )
    parser.add_argument(
        "--enable-remote-debugging",
        type=int,
        nargs="?",
        const=3000,
        help="Enable remote debugging on the specified port (default: 3000)",
    )
    parser.add_argument(
        "--enable-remote-debugging-wait",
        type=int,
        nargs="?",
        const=3000,
        help="Enable remote debugging and wait for the debugger to attach on the specified port (default: 3000)",
    )
    parser.add_argument(
        "--log-dir", type=str, default=log_dir_env, help="Directory to store logs"
    )
    parser.add_argument(
        "--console-logging",
        action="store_true",
        default=str_to_bool(console_logging_env),
        help="Enable logging to the console (can only be enabled if --enable-web-server is true)",
    )
    parser.add_argument("--provider", type=str, help="Provider name")

    # VS Code arguments
    parser.add_argument("--log-file", type=str, help="Log file")
    parser.add_argument("--tracing-level", type=str, help="Tracing level")
    parser.add_argument("--application-name", type=str, help="Application name")
    parser.add_argument("--data-path", type=str, help="Data path")
    parser.add_argument(
        "--enable-sql-authentication-provider",
        action="store_true",
        help="Enable SQL authentication provider",
    )

    args = parser.parse_args()
    return args, config


def get_loggers(log_dir: str) -> logging.Logger:
    # Create the output logger
    logger = logging.getLogger("ossdbtoolsservice")
    try:
        os.makedirs(log_dir, exist_ok=True)
        handler = logging.FileHandler(os.path.join(log_dir, "ossdbtoolsservice.log"))
    except Exception:
        handler = logging.NullHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


def main(
    server: MessageServer,
    args: argparse.Namespace,
    logger: logging.Logger,
) -> None:
    # See if we have any arguments
    wait_for_debugger = False

    # Handle remote debugging
    if args.enable_remote_debugging or args.enable_remote_debugging_wait:
        port = args.enable_remote_debugging or args.enable_remote_debugging_wait
        try:
            print("Starting debugpy on port: " + str(port))
            print("Logs will be stored in ./debugpy_logs")
            os.environ["DEBUGPY_LOG_DIR"] = "./debugpy_logs"  # Path to store logs
            os.environ["GEVENT_SUPPORT"] = "True"  # Path to store logs
            # Dynamically set the Python interpreter for debugpy fron an environment variable or default to the current interpreter.
            python_path = os.getenv("PYTHON", default=sys.executable)
            print("Python path: " + python_path)
            debugpy.configure(python=python_path)
            debugpy.listen(("0.0.0.0", port))
        except BaseException:
            # If port 3000 is used, try another debug port
            port += 1
            debugpy.listen(("0.0.0.0", port))
        if args.enable_remote_debugging_wait:
            wait_for_debugger = True

    # Add console logging if requested
    if args.console_logging:
        if not args.enable_web_server:
            raise ValueError(
                "--console-logging can only be enabled if --enable-web-server is true"
            )
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logger.handlers[0].formatter)
        logger.addHandler(console_handler)

    # Wait for the debugger to attach if needed
    if wait_for_debugger:
        logger.debug("Waiting for a debugger to attach...")
        debugpy.wait_for_client()

    logger.info("PG Tools Service is starting up...")

    # Generate Markdown if the feature switch is enabled
    if args.generate_markdown:
        markdown.generate_requests_markdown(server, logger)
    else:
        # Start the server
        server.start()
        server.wait_for_exit()
