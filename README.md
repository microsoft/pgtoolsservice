# PostgreSQL Tools Service
pgsqltoolsservice is a PostgreSQL implementation of the Data Management Protocol server. It is based on the [Microsoft SQL Tools Service](https://github.com/Microsoft/sqltoolsservice) and [pgAdmin](https://www.pgadmin.org).

# Contributing

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/). For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Developing the PostgreSQL Tools Service
1. Ensure that Python3.6 or above is installed - older versions of Python may work but are not supported
    - Note that when these instructions refer to 'python3' or 'pip3' you may need to use the commands 'python' or 'pip' instead if you are on Windows
2. Run `pip3 install -r requirements.txt` from the root of the project
    - If you need to install pip, see [pip Installation](https://pip.pypa.io/en/latest/installing/)

## Before Committing
We follow Python's [PEP 8 style guide](https://www.python.org/dev/peps/pep-0008) with a maximum line length of 160 characters. To ensure that your code has no style problems, run the following commands before committing (install them from pip first if needed):
1. Run autopep8 to format your code according to PEP 8
    - `autopep8 --in-place --aggressive --aggressive --max-line-length 160 -r .` (from the project's root directory)
2. Run flake8 to look for problems that need to be resolved manually
    - On Mac/Linux: `./scripts/flake8.sh`
    - On Windows: `.\scripts\flake8.ps1`

## Running Tests
The following directions can be used to run all tests:
1. Run `pip3 install -r requirements.txt` if you haven't already
2. `nosetests` (from the project's base directory)
    - To run with coverage:
        1. `nosetests --with-coverage --cover-package="pgsqltoolsservice,pgsmo" --cover-html`
        2. `open cover/index.html` (to view coverage results)

If you only want to run **unit tests**, replace `nosetests` in the above directions with `./scripts/test-unit.sh` or `scripts\test-unit.ps1` as needed for your platform.

If you only want to run **integration tests**, replace `nosetests` in the above directions with `./scripts/test-integration.sh` or `scripts\test-integration.ps1` as needed for your platform. See the section below for more specific details on integration tests.

You can also use `scripts/test-all.sh` or `scripts\test-all.ps1` to run all tests instead of using the `nosetests` command. All of these scripts will accept any arguments that you give and pass them directly to `nosetests`.

To run tests in VS Code editor, add the following in VS Code settings: `"python.unitTest.nosetestsEnabled": true`  

## Integration Tests
The PostgreSQL Tools Service supports tests that connect to a real Postgres database, which we call integration tests. These can be run by calling `./scripts/test-integration.sh` or `scripts\test-integration.ps1` from the project's root directory.

### Configuring Integration Tests
Integration tests require a local config file that contains the options for connecting to your test database. The template config file is located in `tests/integration_tests/config.json.txt`. Copy this file to `tests/integration_tests/config.json` and modify values as appropriate. The template lists the most common options, but any options that can be used when establishing a psycopg2 connection can also be set in the config file. You can put multiple server configurations in the file in order to run each integration test multiple times, once per server.

### Creating Integration Tests
Integration tests can be inserted in line with our unit tests. The `tests.integration` module exports a `integration_test` decorator and a `get_connection` function that can be used in integration tests.

To declare that a test is an integration test, mark it with the imported `@integration_test` decorator. This will automatically patch `psycopg2.connect` in your test to return the test database connection from your config file, and will let you use the `get_connection` function to retrieve that connection if you need it elsewhere. You can optionally pass `min_version` and `max_version` integer arguments to the `@integration_test` decorator to make the test only run when connected to the specified versions of Postgres. You can also use the `create_extra_test_database` function if your test needs additional databases.

Each integration test will run with its own database, which will be created before the test starts and dropped when the test ends.

You can find an integration test example in code in `tests/query_execution/test_query_execution_service.py`'s `test_query_execution_and_retrieval` method.

### Creating End-to-End JSON RPC Integration Tests
You can also create end-to-end JSON RPC integration tests, which test the entire service using JSON RPC inputs and outputs. An example of these tests is located in `tests/json_rpc_tests/object_explorer_json_rpc_tests.py`.

When creating one of these tests, mark the test with an integration test decorator as usual. Then, create `tests.json_rpc_tests.RPCTestMessage` objects for each message to send as part of the test, including any connection messages that are needed. Finally, initialize a `tests.json_rpc_tests.JSONRPCTestCase` object with the ordered list of messages to send, and call its `.run()` method to run the test.

When creating each `tests.json_rpc_tests.RPCTestMessage`, you should include a response verification callback that will be called with the response as a parameter, deserialized as a dictionary, when the server responds to the request. You should also include a list of notification verifiers. Each verifier is a tuple consisting of two functions. The first function is a filter function that will be called to determine which single notification the verifier applies to. If the verifier function returns true for multiple notifications, the first one will be used. The second function is a callback that will be called with the notification as a parameter, deserialized as a dictionary.

## Manual Testing
1. Update your PYTHONPATH environment variable to contain the source directory. From within the project's main directory, run the following commands:
    - On Mac/Linux: `export PYTHONPATH=$(pwd)`
    - On Windows: `set PYTHONPATH=%cd%`
2. `python3 pgsqltoolsservice/pgtoolsservice_main.py`
3. Now you can pass in JSON RPC requests to stdin, following the [language server protocol specifications](https://github.com/Microsoft/language-server-protocol/blob/master/protocol.md).

## Remote Debugging with VS Code
It is possible to remotely attach a debugger to the PostgreSQL Tools Service through VS Code's Python extension. Just start the service with the command line argument `--enable-remote-debugging` and then, from the debug tab in VS Code, click 'Attach (Remote Debug)'.

If you want to debug startup, use the flag `--enable-remote-debugging-wait` instead, and the service will wait for you to attach the debugger before starting up.

By default, the remote debugging server runs on port 3000. If you need to use a different port, just pass it as the argument to that flag, e.g. `--enable-remote-debugging=3001`

### Remote Debugging with Carbon
You can set configuration options in Carbon to let you attach the remote debugger to the PostgreSQL Tools Service running inside Carbon. Set `pgsql.useDebugSource` to true and set `pgsql.debugSourcePath` to the path to the root of your PostgreSQL Tools Service repo (i.e. the folder containing this readme file). If you want to debug startup, also set `pgsql.enableStartupDebugging` to true. Here are examples from a settings.json file:

```
    "pgsql.debugSourcePath": "/Users/mairvine/code/pgsqltoolsservice",
    "pgsql.useDebugSource": true,
    "pgsql.enableStartupDebugging": true
```
If you get "ptvsd module not found" error - ensure you have python 3 or above installed and user environment variable "path" pointing to latest python scripts. For eg. on a windows machine path value looks like "< path to current useraccount >\APPDATA\LOCAL\PROGRAMS\PYTHON\PYTHON36\SCRIPTS\".

## Building Executables
To build an executable, run the following commands starting from the main source code directory on the platform you want to build for. The output will be placed in a folder called build.
- On Mac: `./scripts/build-mac.sh`
    - The output will be placed in the build/pgtoolsservice directory
- On Linux: `./scripts/build-linux.sh`
- On Windows: `.\scripts\build.ps1`
    - Or, from cmd.exe: `powershell.exe scripts\build.ps1`
