# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds the error resources for ossdb tools service errors"""

from .OssdbErrorConstants import OssdbErrorConstants
from .OssdbErrorResource import OssdbErrorResource


class OssdbErrorCodes():

    """ AZURE MYSQL FLEXIBLE SERVER CONNECTION ERROR CODES """

    def MYSQL_FLEX_SSL_REQUIRED_NOT_PROVIDED(errcode: int, errmsg: str):
        return OssdbErrorResource(
            OssdbErrorConstants.MYSQL_FLEX_SSL_REQUIRED_NOT_PROVIDED_CODE,
            errcode,
            errmsg,
            OssdbErrorConstants.MYSQL_FLEX_SSL_REQUIRED_NOT_PROVIDED_CAUSES,
            OssdbErrorConstants.MYSQL_FLEX_SSL_REQUIRED_NOT_PROVIDED_SUGGESTIONS
        )

    def MYSQL_FLEX_IP_NOT_WHITELISTED(errcode: int, errmsg: str):
        return OssdbErrorResource(
            OssdbErrorConstants.MYSQL_FLEX_IP_NOT_WHITELISTED_CODE,
            errcode,
            errmsg,
            None,
            OssdbErrorConstants.MYSQL_FLEX_IP_NOT_WHITELISTED_SUGGESTIONS
        )

    def MYSQL_FLEX_INCORRECT_CREDENTIALS(errcode: int, errmsg: str):
        return OssdbErrorResource(
            OssdbErrorConstants.MYSQL_FLEX_INCORRECT_CREDENTIALS_CODE,
            errcode,
            errmsg,
            OssdbErrorConstants.MYSQL_FLEX_INCORRECT_CREDENTIALS_CAUSES,
            OssdbErrorConstants.MYSQL_FLEX_INCORRECT_CREDENTIALS_SUGGESTIONS
        )

    def MYSQL_SSL_CA_REQUIRED_FOR_VERIFY_MODE():
        return OssdbErrorResource(
            OssdbErrorConstants.MYSQL_SSL_CA_REQUIRED_FOR_VERIFY_MODES_CODE,
            None,
            OssdbErrorConstants.MYSQL_SSL_CA_REQUIRED_FOR_VERIFY_MODES_ERRMSG,
            None,
            OssdbErrorConstants.MYSQL_SSL_CA_REQUIRED_FOR_VERIFY_MODES_SUGGESTIONS
        )
    
    def MYSQL_DRIVER_UNKNOWN_ERROR(errcode: int, errmsg: str):
        return OssdbErrorResource(
            errcode if errcode else OssdbErrorConstants.MYSQL_DRIVER_UNKNOWN_ERROR_CODE,
            errcode,
            errmsg,
            None,
            None
        )