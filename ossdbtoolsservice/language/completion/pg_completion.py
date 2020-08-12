# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from prompt_toolkit.completion import Completion    # noqa


class PGCompletion(Completion):
    """
    This class extends prompt_toolkit.completion class to include specific fields (eg. schema)
    while sending completions based on token text in pgcompleter.
    """

    def __init__(self, text, start_position=0, display=None, display_meta=None,
                 style='', schema=None):
        self.schema = schema
        super(PGCompletion, self).__init__(text, start_position, display, display_meta,
                                           style)
