"""Listen for JSON RPC inputs on stdin and dispatch them to the appropriate methods"""

import sys
from jsonrpc import JSONRPCResponseManager, dispatcher
from connection_service import ConnectionService
from contracts.initialization import InitializeResult

class Server(object):
    """Class representing a server for JSON RPC requests"""

    def __init__(self):
        self.connection_service = ConnectionService()
        self.is_shutdown = False
        self.should_exit = False
        dispatcher['initialize'] = self.initialize

    def initialize(self):
        """Initialize the service"""
        self.initialize_dispatcher()
        return InitializeResult().json

    def initialize_dispatcher(self):
        """Initialize the JSON RPC dispatcher"""
        dispatcher['connection/connect'] = self.connection_service.connect
        dispatcher['connection/disconnect'] = self.connection_service.disconnect
        dispatcher['shutdown'] = self.shutdown
        dispatcher['exit'] = self.exit
        dispatcher['echo'] = echo

    def shutdown(self):
        """Shutdown the service"""
        self.is_shutdown = True

    def exit(self):
        """Exit the process"""
        self.should_exit = True

def echo(arg):
    """Function used for manually testing the JSON RPC server"""
    print arg

def handle_input():
    """Loop to process input and dispatch the requests"""
    while True:
        somestring = sys.stdin.read()
        response = JSONRPCResponseManager.handle(somestring, dispatcher)
        if SERVER.should_exit:
            sys.exit(0 if SERVER.is_shutdown else 1)
        print response.json

if __name__ == '__main__':
    SERVER = Server()
    SERVER.initialize_dispatcher()
    handle_input()
