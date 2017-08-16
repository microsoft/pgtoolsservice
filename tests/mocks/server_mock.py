# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from unittest import mock


class ServerMock():

    def __init__(self):
        self.set_request_handler = mock.MagicMock()
