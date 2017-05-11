# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Listen for JSON RPC inputs on stdin and dispatch them to the appropriate methods"""

from __future__ import print_function
import logging
import sys
import utils
from connection_service import ConnectionService
from contracts.capabilities_service import (
    CapabilitiesResult,
    ConnectionProviderOptions,
    ConnectionOption,
    DMPServerCapabilities)
from contracts.initialization import (
    InitializeResult,
    ServerCapabilities,
    TextDocumentSyncKind)
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
        initialize_result = InitializeResult(ServerCapabilities(
            textDocumentSync=TextDocumentSyncKind.INCREMENTAL,
            definitionProvider=False,
            referencesProvider=False,
            documentFormattingProvider=False,
            documentRangeFormattingProvider=False,
            documentHighlightProvider=False,
            hoverProvider=False,
            completionProvider=None
        ))
        # Since jsonrpc expects a serializable object, convert it to a
        # dictionary
        return utils.object_to_dictionary(initialize_result)

    def initialize_dispatcher(self):
        """Initialize the JSON RPC dispatcher"""
        logging.debug('initialize_dispatcher method')
        dispatcher['connection/connect'] = self.connection_service.connect
        dispatcher['connection/disconnect'] = self.connection_service.disconnect
        dispatcher['shutdown'] = self.shutdown
        dispatcher['exit'] = self.exit
        dispatcher['echo'] = echo
        dispatcher['version'] = version
        dispatcher['capabilities/list'] = capabilities

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


def version():
    """Get the version of the tools service"""
    return "0"


def capabilities(hostName, hostVersion):
    """Get the server capabilities response"""
    server_capabilities = CapabilitiesResult(DMPServerCapabilities(
        protocolVersion='1.0',
        providerName='PGSQL',
        providerDisplayName='PostgreSQL',
        connectionProvider=ConnectionProviderOptions(options=[ConnectionOption(
            name='connectionString',
            displayName='Connection String',
            description='PostgreSQL-format connection string',
            valueType='string',
            isIdentity=True,
            isRequired=True,
            groupName='Source'
        )])
    ))
    # Since jsonrpc expects a serializable object, convert it to a dictionary
    return utils.object_to_dictionary(server_capabilities)


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
        if response is None:
            continue
        response_text = 'Content-Length: {}\r\n\r\n'.format(
            len(response.json)) + response.json
        logging.debug('sending response: %s', response_text)
        sys.stdout.write(response_text)
        sys.stdout.flush()


if __name__ == '__main__':
    logging.basicConfig(filename='server.log', level=logging.DEBUG)
    logging.debug('initializing server')
    SERVER = Server()
    handle_input()
