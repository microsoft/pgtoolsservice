# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds the error resource for ossdb tools service errors"""
class OssdbErrorResource():

    def __init__(self, code: int, msg: str, causes: str, suggestions: str):
        self._code = code
        self._msg = msg
        self._causes = causes
        self._suggestions = suggestions
        self._userErrMsg = self._buildUserErrMsg()
    
    def __str__(self) -> str:
        return self._userErrMsg
    
    @property
    def code(self) -> int:
        return self._code
    
    @property    
    def userErrMsg(self) -> str:
        return self._userErrMsg
    
    def _buildUserErrMsg(self) -> str:
        usermsg = "Error Message : " + self._msg;
        if self._code:
            usermsg += "\nInternalErrorCode : " + str(self._code)
        if self._causes:
            usermsg += "\nCauses : " + self._causes
        if self._suggestions:
            usermsg += "\nSuggestions : " + self._suggestions
        return usermsg