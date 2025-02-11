import asyncio
import threading


class AsyncRunner:
    """Runs async functions in a dedicated event loop thread."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        """Runs the event loop."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run(self, coro):
        """Submits a coroutine to the event loop and returns a Future."""
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()

    def shutdown(self):
        """Stops the event loop cleanly."""
        self.loop.call_soon_threadsafe(self.loop.stop())
        self.thread.join()
