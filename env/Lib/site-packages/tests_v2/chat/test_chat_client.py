"""A simple chat client that connects to the PostgreSQL language server
and sends chat completion requests.

This requires that PGTS_CHAT_USE_AZURE_OPENAI be set to true in the environment variables,
and the relevant Azure OpenAI environment variables be set as well.
"""

import contextlib
import json
import subprocess
import sys
import threading
from io import FileIO
from queue import Queue
from typing import IO, Any

import click
from rich.console import Console

PRINT_STDERR = False


def read_responses(stdout_wrapped: FileIO, queue: Queue[str]) -> None:
    """Read responses from the server's stdout."""
    chat_response = None
    while True:
        header_bytes = stdout_wrapped.readline()
        if not header_bytes:
            break
        try:
            header = header_bytes.decode("utf-8").strip()
            if header.startswith("Content-Length:"):
                length = int(header.split(":")[1].strip())
                stdout_wrapped.readline()  # Read the empty line
                body = stdout_wrapped.read(length)
                message = json.loads(body.decode("utf-8"))
                if "error" in message:
                    print(f"Error response: {message['error']['message']}")
                elif "method" in message and message["method"] == "connection/complete":
                    queue.put("Connected to database.")
                elif "method" in message and message["method"] == "chat/completion-result":
                    # print("RECV <----------")
                    # space = "     "
                    # print(
                    #     space
                    #     + f"\n{space}".join(json.dumps(message, indent=2).split("\n"))
                    # )
                    # print("<---------------")

                    params = message["params"]
                    content = params["content"]

                    if content:
                        print(content, end="")

                    if chat_response is None:
                        chat_response = params["content"] or ""
                    else:
                        chat_response += params["content"] or ""
                    if params["isComplete"] and chat_response:
                        queue.put(chat_response)
                        chat_response = None
                else:
                    print("RECV <----------")
                    space = "     "
                    print(
                        space + f"\n{space}".join(json.dumps(message, indent=2).split("\n"))
                    )
                    print("<---------------")

        except Exception as e:
            print(f"Error reading response: {e}")
    print("Server stopped.")


def read_stderr(stderr: IO[bytes]) -> None:
    """Read responses from the server's stderr."""
    while True:
        line = stderr.readline()
        if not line:
            break
        print("STDERR:", line.strip())
    print("Server stopped.")


def send_message(stdin_wrapped: FileIO, message: dict[str, Any]) -> None:
    """Send a message to the server."""
    HEADER = "Content-Length: {}\r\n\r\n"
    json_content = json.dumps(message, sort_keys=True)
    header = HEADER.format(str(len(json_content)))
    stdin_wrapped.write(header.encode("ascii"))
    stdin_wrapped.write(json_content.encode("utf-8"))
    stdin_wrapped.flush()
    print("SEND ---------->")
    space = "     "
    print(space + f"\n{space}".join(json.dumps(message, indent=2).split("\n")))
    print("--------------->")


def send_chat_completion_message(
    stdin_wrapped: FileIO, user_input: str, history: list[dict[str, str]]
) -> None:
    request = {
        "jsonrpc": "2.0",
        "method": "chat/completion-request",
        "params": {
            "ownerUri": "test",
            "prompt": user_input,
            "history": history,
        },
        "id": 954123,
    }

    # Send the JSON-RPC request to the server's stdin
    send_message(stdin_wrapped, request)


def chat_with_postgresql() -> None:
    console = Console()

    print("Starting the language server...")
    # Start the language server process
    process = subprocess.Popen(
        [
            sys.executable,
            "ossdbtoolsservice_main.py",
            "--log-dir",
            "/home/rob/proj/vscode/pgtoolsservice/zignore-logs",
            "--console-logging",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None

    with (
        open(process.stdin.fileno(), "wb", buffering=0, closefd=False) as stdin_wrapped,
        open(process.stdout.fileno(), "rb", buffering=0, closefd=False) as stdout_wrapped,
    ):
        print("Language server started.")
        print("Creating connection to database...")

        send_message(
            stdin_wrapped,
            {
                "jsonrpc": "2.0",
                "method": "connection/connect",
                "id": 12345,
                "params": {
                    "ownerUri": "test",
                    "type": "Query",
                    "connection": {
                        "options": {
                            "host": "localhost",
                            "port": 5432,
                            "user": "postgres",
                            "password": "example",
                            "dbname": "postgres",
                        },
                    },
                },
            },
        )

        queue = Queue[str]()

        # Start a thread to handle asynchronous responses from the server
        response_thread = threading.Thread(
            target=read_responses, args=(stdout_wrapped, queue), daemon=True
        )
        response_thread.start()

        queue.get()  # Wait for the connection to complete

        if PRINT_STDERR:
            stderr_thread = threading.Thread(
                target=read_stderr, args=(process.stderr,), daemon=True
            )
            stderr_thread.start()
        else:
            stderr_thread = None

        try:
            console.print(
                "[italic]Welcome to the PostgreSQL chat bot! "
                "Type 'exit' to exit the chat.[/italic]\n"
            )

            chatting = True
            history: list[dict[str, str]] = []
            while chatting:
                try:
                    user_input = console.input("[bold]User :>[/bold] ")
                    print()
                except KeyboardInterrupt:
                    print("\n\nExiting chat...")
                    break
                except EOFError:
                    print("\n\nExiting chat...")
                    break

                if user_input == "exit":
                    print("\n\nExiting chat...")
                    break
                send_chat_completion_message(stdin_wrapped, user_input, history)
                print("🐘 :>")
                print()
                result = queue.get()
                print()
                print()
                history.append({"participant": "user", "content": user_input})
                history.append({"participant": "assistant", "content": result})
                chatting = True

        finally:
            with contextlib.suppress(Exception):
                send_message(
                    stdin_wrapped,
                    {
                        "jsonrpc": "2.0",
                        "method": "exit",
                        "id": 21451,
                        "params": None,
                    },
                )
            process.terminate()
            process.wait()
            response_thread.join()
            if stderr_thread:
                stderr_thread.join()


@click.group()
def cli() -> None:
    """PostgreSQL Copilot."""
    pass


@cli.command()
def chat() -> None:
    """Chat with your database."""
    chat_with_postgresql()


if __name__ == "__main__":
    cli()
