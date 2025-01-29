import asyncio
import subprocess
import json
import sys
from typing import Any


async def read_responses(stdout_reader: asyncio.StreamReader):
    """Read responses from the server's stdout."""
    while True:
        header = await stdout_reader.readline()
        if not header:
            break
        try:
            header = header.decode("utf-8").strip()
            if header.startswith("Content-Length:"):
                length = int(header.split(":")[1].strip())
                await stdout_reader.readline()  # Read the empty line
                body = await stdout_reader.readexactly(length)
                message = body.decode("utf-8")
                print("RECV <---")
                space = "    "
                msg_txt = space + json.dumps(json.loads(message), indent=2).replace(
                    "\n", "\n" + space
                )
                print(msg_txt)
        except Exception as e:
            print(f"Error reading response: {e}")
    print("Server stopped.")


async def read_stderr(stderr_reader: asyncio.StreamReader):
    """Read responses from the server's stderr."""
    while True:
        line = await stderr_reader.readline()
        if not line:
            break
        print("STDERR:", line.decode("utf-8").strip())
    print("Server stopped.")


async def send_message(stdin_writer: asyncio.StreamWriter, message: dict[str, Any]):
    """Send a message to the server."""
    HEADER = "Content-Length: {}\r\n\r\n"
    json_content = json.dumps(message, sort_keys=True)
    header = HEADER.format(str(len(json_content)))
    stdin_writer.write(header.encode("ascii"))
    stdin_writer.write(json_content.encode("utf-8"))
    await stdin_writer.drain()
    print("SENT --->")
    space = "    "
    msg_txt = space + json.dumps(message, indent=2).replace("\n", "\n" + space)
    print(msg_txt)


async def main():
    DISPLAY_STDERR = False

    print("Starting the language server...")
    # Start the language server process
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "ossdbtoolsservice_main.py",
        "--log-dir",
        "/home/rob/proj/vscode/pgtoolsservice/zignore-logs",
        "--console-logging",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    print("Language server started.")
    print("Press enter to exit after messaging.")

    # Start tasks to handle asynchronous responses from the server
    response_task = asyncio.create_task(read_responses(process.stdout))
    if DISPLAY_STDERR:
        stderr_task = asyncio.create_task(read_stderr(process.stderr))
    else:
        stderr_task = None

    try:
        # JSON-RPC request example
        request = {
            "jsonrpc": "2.0",
            "method": "version",
            "params": None,
            "id": 954123,
        }
        # Send the JSON-RPC request to the server's stdin
        await send_message(process.stdin, request)

        await asyncio.get_event_loop().run_in_executor(None, input)

        # Example shutdown request
        shutdown_request = {
            "jsonrpc": "2.0",
            "method": "exit",
            "id": 21451,
            "params": None,
        }
        await send_message(process.stdin, shutdown_request)

    finally:
        process.terminate()
        await process.wait()
        await response_task
        if stderr_task:
            await stderr_task


if __name__ == "__main__":
    asyncio.run(main())
