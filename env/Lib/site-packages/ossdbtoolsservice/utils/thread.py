# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility functions for operating with threads"""

import threading
from typing import Any, Callable


def run_as_thread(function: Callable, *args: Any) -> threading.Thread:
    """Runs a function in a thread, passing in the specified args
    as its arguments and returns the thread"""
    task = threading.Thread(target=function, args=args)
    task.daemon = False
    task.start()
    return task
