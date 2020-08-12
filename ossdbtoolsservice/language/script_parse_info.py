# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from typing import List     # noqa
from prompt_toolkit.completion import Completion    # noqa
from prompt_toolkit.document import Document    # noqa


class ScriptParseInfo(object):
    """Represents information about a parsed document used in autocomplete"""

    def __init__(self):
        self.connection_key: str = None
        self.is_connected: bool = False
        self.document: Document = None
        self.current_suggestions: List[Completion] = None

    def can_queue(self) -> bool:
        """Can this be put in a queued operation?"""
        return self.connection_key is not None
