# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from typing import List  # noqa
from prompt_toolkit.completion import Completion  # noqa
from prompt_toolkit.document import Document  # noqa


class ScriptParseInfo:
    """Represents information about a parsed document used in autocomplete"""

    def __init__(self) -> None:
        self.connection_key: str | None = None
        self.is_connected: bool = False
        self.document: Document | None = None
        self.current_suggestions: list[Completion] | None = None
