# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from ossdbtoolsservice.serialization import Serializable
from ossdbtoolsservice.workspace.contracts import Range


class TextEdit(Serializable):
    """
    A textual edit applicable to a text document.
    """

    range: Range | None
    new_text: str | None

    @classmethod
    def from_data(cls, text_range: Range | None, new_text: str | None) -> "TextEdit":
        obj = cls()
        obj.range = text_range
        obj.new_text = new_text
        return obj

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[Serializable]]:
        return {"range": Range}

    def __init__(self) -> None:
        self.range = None
        self.new_text = None
