import sys


def is_debugger_active() -> bool:
    return sys.gettrace() is not None
