# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Contains contract classes for service initialization"""


class InitializeResult(object):
    """Initialization result contract"""

    def __init__(self):
        self.json = '{"capabilities": {}}'
