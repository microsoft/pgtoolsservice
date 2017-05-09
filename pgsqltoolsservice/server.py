# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Listen for JSON RPC inputs on stdin and dispatch them to the appropriate methods"""

from __future__ import print_function
import logging
import sys
from connection_service import ConnectionService
from contracts.initialization import InitializeResult
from jsonrpc import JSONRPCResponseManager, dispatcher


class Server(object):
    """Class representing a server for JSON RPC requests"""

    def __init__(self):
        logging.debug('creating server object')
        self.connection_service = ConnectionService()
        self.is_shutdown = False
        self.should_exit = False
        dispatcher['initialize'] = self.initialize

    def initialize(
            self,
            processId=None,
            rootPath=None,
            rootUri=None,
            initializationOptions=None,
            capabilities=None,
            trace=None):
        """Initialize the service"""
        logging.debug('initialize method')
        self.initialize_dispatcher()
        return InitializeResult().json

    def initialize_dispatcher(self):
        """Initialize the JSON RPC dispatcher"""
        logging.debug('initialize_dispatcher method')
        dispatcher['connection/connect'] = self.connection_service.connect
        dispatcher['connection/disconnect'] = self.connection_service.disconnect
        dispatcher['shutdown'] = self.shutdown
        dispatcher['exit'] = self.exit
        dispatcher['echo'] = echo

    def shutdown(self):
        """Shutdown the service"""
        logging.debug('shutdown method')
        self.is_shutdown = True

    def exit(self):
        """Exit the process"""
        logging.debug('exit method')
        self.should_exit = True


def echo(arg):
    """Function used for manually testing the JSON RPC server"""
    print(arg)


def read_headers():
    """Read the VSCode Language Server Protocol message headers"""
    headers = {}
    for line in sys.stdin:
        line = line.strip()
        if line == '':
            return headers
        parts = line.split(': ')
        headers[parts[0]] = parts[1]


def read_content(length):
    """Read the number of bytes of content specified"""
    return sys.stdin.read(length)


def handle_input():
    """
    Loop to process input and dispatch the requests.

    Input is formatted according to the VSCode
    language server protocol at https://github.com/Microsoft/language-server-protocol/. For example
    a single request might look like the following (see more examples in README.md):

    'Content-Length: 57

    {"jsonrpc":"2.0","id":0,"method":"connection/disconnect"}'
    """
    while True:
        headers = read_headers()
        somestring = read_content(int(headers['Content-Length']))
        logging.debug('read string: %s', somestring)
        response = JSONRPCResponseManager.handle(somestring, dispatcher)
        if SERVER.should_exit:
            sys.exit(0 if SERVER.is_shutdown else 1)
        logging.debug('sending response: %s', response.json)
        print(response.json)


if __name__ == '__main__':
    logging.basicConfig(filename='server.log', level=logging.DEBUG)
    logging.debug('initializing server')
    SERVER = Server()
    handle_input()
