# PostgreSQL Tools Service
pgsqltoolsservice is a PostgreSQL implementation of the Data Management Protocol server. It is based on the [Microsoft SQL Tools Service](https://github.com/Microsoft/sqltoolsservice) and [pgAdmin](https://www.pgadmin.org).

# Contributing

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Developing the PostgreSQL Tools Service
1. Ensure that Python2.7 or above is installed - Python3 is supported (you will have to use python3 or pip3 in place of python or pip commands in this guide)
2. Run `pip install -r requirements.txt` from the root of the project
    - If you need to install pip, see [https://pip.pypa.io/en/latest/installing/]()

## Running Tests
1. `pip install nose`
2. `nosetests` (from the project's base directory)

## Manual Testing
1. `python pgsqltoolsservice/server.py`
2. Now you can pass in JSON RPC requests to stdin, following the [language server protocol specifications](https://github.com/Microsoft/language-server-protocol/blob/master/protocol.md). The following commands are supported currently:
    - initialize
    - connection/connect
    - connection/disconnect
    - shutdown
    - exit
    - version
    - capabilities/list

### Example Inputs
```
Content-Length: 106

{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"processId":4155,"capabilities":{},"trace":"off"}}Content-Length: 44

{"jsonrpc":"2.0","id":0,"method":"shutdown"}Content-Length: 40

{"jsonrpc":"2.0","id":0,"method":"exit"}
```

```
Content-Length: 106

{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"processId":4155,"capabilities":{},"trace":"off"}}Content-Length: 170

{"jsonrpc":"2.0","id":0,"method":"connection/connect","params":{"connectionstring":"dbname=postgres user=postgres password=password host=MAIRVINE-PC connect_timeout=10"}}Content-Length: 57

{"jsonrpc":"2.0","id":0,"method":"connection/disconnect"}Content-Length: 40

{"jsonrpc":"2.0","id":0,"method":"exit"}
```
