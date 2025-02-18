import asyncio
import threading
from collections.abc import Coroutine
from concurrent.futures import Future
from typing import Any


class AsyncRunner:
    """Runs async functions in a dedicated event loop thread.

    If an event loop is already running, it uses that loop.
    Otherwise, it creates a new one in a dedicated thread.
    This is useful for running async functions in a synchronous context.
    """

    def __init__(self) -> None:
        self._existing_loop = False
        try:
            self.loop = asyncio.get_running_loop()
            self._existing_loop = True
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

    def _run_loop(self) -> None:
        """Runs the event loop."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coroutine: Coroutine) -> Any:
        """Submits a coroutine to the event loop and waits for it to complete."""
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result()

    def run_async(self, coroutine: Coroutine) -> Future:
        """Submits a coroutine to the event loop without waiting for it to complete."""
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop)

    def shutdown(self) -> None:
        """Stops the event loop cleanly."""
        if not self._existing_loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join()
