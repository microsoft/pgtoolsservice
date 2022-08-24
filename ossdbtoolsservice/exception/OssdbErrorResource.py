# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds the error resource for ossdb tools service errors"""
class OssdbErrorResource():

    def __init__(self, internalErrorCode: int, errcode: int, errmsg: str, causes: str, suggestions: str):
        self._internalErrorCode = internalErrorCode
        self._errcode = errcode
        self._errmsg = errmsg
        self._causes = causes
        self._suggestions = suggestions
        self._userErrMsg = self._buildUserErrMsg()
    
    def __str__(self) -> str:
        return self._userErrMsg
    
    @property
    def internalErrorCode(self) -> int:
        return self._internalErrorCode
    
    @property    
    def userErrMsg(self) -> str:
        return self._userErrMsg
    
    def _buildUserErrMsg(self) -> str:
        usermsg = "Error Message : " + self._errmsg;
        if self._errcode:
            usermsg += "\nErrorCode : " + str(self._errcode)
        if self._causes:
            usermsg += "\nCauses : " + self._causes
        if self._suggestions:
            usermsg += "\nSuggestions : " + self._suggestions
        return usermsg