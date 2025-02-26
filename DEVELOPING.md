## Development Installation

To install the package in development mode, run:

    pip install -e .[dev]

This installs an editable version of the package with extra development dependencies.
This is required for running the VS Code extension in development.

## Developing on Windows vs Linux/Mac

This project is set up to be developed on Windows, Linux, or Mac, but there are some convenience scripts
that are written in bash that may not have corresponding PowerShell scripts. Windows with WSL2 linux
is a great option for developing on this project. If you develop on windows and are missing
some convenience scripts, contributions welcome!

## Running tests

There are two test projects in the repository, `tests` and `tests_v2`.
The `tests_v2` are newer tests that are run with pytest.

To run all tests, run: `scripts/test_all.sh` or `scripts/test_all.ps1` if you are on Windows.

To run linting checks, use `scripts/lint.sh` or `scripts/lint.ps1` if you are on Windows.

## Formatting

You can run

```
scripts/format.sh
```

to format the code with ruff.

## Docker development database

To run the integration tests, which are marked across the `tests` with a `@integration` decorator, you need to have a running postgres instance.
You can use the `docker-compose` file to quickly spin up a local postgres instance.

```bash
docker-compose up -d
```
This will create a local postgres instance with the following connection string:

```
postgresql://postgres:example@localhost:5432/postgres
```

## Loading test data

Load in test datasets using the script

```
scripts/load_test_data.sh <dataset-name> --connection-string <connection-string>
```

If the connection string is not provided, it will use the default connection string for the 
`docker-compose.yml` file.

### Playback tests

The `tests_v2` project contains "playback" tests. These are tests that play back a recorded session to a server and verify
that the server responds with the expected results.

Server messages have some non-deterministic values, and the playback accounts for these by using a configurable process of
ignoring certain properties, replacing values in subsequent messages, or utilizing custom match functions. See the
`PlaybackConfiguration` class for more details.

#### Recording a session for a playback test

A recorded session happens by giving PGTS command arguments and interacting with the server. For VSCode, this is done by
providing a PGTS_RECORD_MESSAGES_TO_FILE environment variable in the launch.json file and running a debug session of the extension.
The value of the environment variable is the path to a file where the recorded session will be saved.

An important aspect of recording a session for a playback test is that the database initialization must be exactly the same for the
recorded session and playback. The steps to do this are as follows:

1. Create a fresh docker image that is freshly loaded with data. Do this by running the following command:

Use the docker-compose.recording.yml file to create a docker image with a fresh database. The below
command ensures that any previous containers are removed and a new one is created.

```bash
docker-compose -f docker-compose.recording.yml rm -f  
docker-compose -f docker-compose.recording.yml up -d
```

Note that this runs the server on port 5678, to avoid conflicts with other running servers.

2. Load in the test dataset using the load_test_data.sh script. For example, to load the `pagila` dataset, run:

```bash
scripts/load_test_data.sh pagila --connection-string postgresql://postgres:example@localhost:5678/postgres
```

3. Run the VSCode extension with the PGTS_RECORD_MESSAGES_TO_FILE environment variable set to the path of the file where you want to save the recorded session.
4. Interact with the server in the VSCode extension to generate the messages you want to record.
5. Stop the server and the VSCode extension. The recorded session will be saved to the file you specified in step 3.
6. Copy the recorded session file to the tests_v2/test_data/recordings folder.
7. Add a test that plays back the recorded session. See the tests in the tests_v2/playback_tests folder for examples.
8. If the test fails due to non-deterministic values, update the recorded session file to ignore those values. See the `PlaybackConfiguration` class for more details.

#### Recorded session format

The recorded session is a JSON file that is organized into "client_request_groups". Each group contains a client request and the corresponding server response,
as well as any server notifications, client notifications, and server request/client response pairs that occurred during the time between the group's client request
and the next client request. This organizes the recorded session into logical groups of messages that are dictated by client requests, which are normally the drivers
of the communication. Note that, in addition to being a format that can be played back against a server, it is also good for debugging and understanding the communication between the client and server.

See the [tests_v2/test_data/recordings](tests_v2/test_data/recordings) folder for examples of recorded sessions.
