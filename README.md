# PostgreSQL Tools Service
pgsqltoolsservice is a PostgreSQL implementation of the Data Management Protocol server. It is based on the [Microsoft SQL Tools Service](https://github.com/Microsoft/sqltoolsservice) and [pgAdmin](https://www.pgadmin.org).

# Contributing

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Developing the PostgreSQL Tools Service
1. Ensure that Python2.7 or above is installed - Python3 is supported
2. Run `pip install -r requirements.txt` from the root of the project

## Running Tests
1. `pip install nose`
2. `nosetests` (from the project's base directory)

## Manual Testing
1. `python pgsqltoolsservice/server.py`
2. Now you can pass in JSON RPC requests to stdin, terminated with a newline followed by EOF (ctrl+D). E.g.:
    1. `{"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": []}`
    2. `{"jsonrpc": "2.0", "id": 0, "method": "echo", "params": ["Hello world!"]}`
    3. `{"jsonrpc": "2.0", "id": 0, "method": "connection/connect", "params": ["dbname=postgres user=postgres password=password host=MAIRVINE-PC connect_timeout=10"]}`
    4. `{"jsonrpc": "2.0", "id": 0, "method": "connection/disconnect", "params": []}`
    5. `{"jsonrpc": "2.0", "id": 0, "method": "shutdown", "params": []}`
    6. `{"jsonrpc": "2.0", "id": 0, "method": "exit", "params": []}`