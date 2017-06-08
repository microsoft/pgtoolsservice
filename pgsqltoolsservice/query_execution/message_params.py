# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

class MessageParams(object):

    def __init__(self, message, owner_uri):
        self.message = message
        self.ownerUri = owner_uri
    