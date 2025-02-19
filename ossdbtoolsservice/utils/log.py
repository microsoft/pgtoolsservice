# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Utility functions for logging"""

from logging import Logger


def log_debug(logger: Logger | None, message: str) -> None:
    """Logs message to debug if logger exists"""
    if logger is not None:
        logger.debug(message)
