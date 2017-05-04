"""Listen for JSON RPC inputs on stdin and dispatch them to the appropriate methods"""

import sys
from jsonrpc import JSONRPCResponseManager, dispatcher
from connection_service import ConnectionService

class Server(object):
    """TODO"""

    def __init__(self):
        self.connection_service = ConnectionService()

    def initialize_dispatcher(self):
        """TODO"""
        dispatcher['connection/connect'] = self.connection_service.connect
        dispatcher['connection/disconnect'] = self.connection_service.disconnect
        dispatcher['echo'] = echo

def echo(arg):
    """TODO"""
    print arg

def handle_input():
    """TODO"""
    while True:
        somestring = sys.stdin.read()
        response = JSONRPCResponseManager.handle(somestring, dispatcher)
        print response.json

if __name__ == '__main__':
    SERVER = Server()
    SERVER.initialize_dispatcher()
    handle_input()
