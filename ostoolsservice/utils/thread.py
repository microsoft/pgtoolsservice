# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility functions for operating with threads"""

import threading  # noqa
from typing import Callable     # noqa


def run_as_thread(function: Callable, *args) -> threading.Thread:
    """Runs a function in a thread, passing in the specified args as its arguments and returns the thread"""
    task = threading.Thread(target=function, args=args)
    task.setDaemon(False)
    task.start()
    return task
