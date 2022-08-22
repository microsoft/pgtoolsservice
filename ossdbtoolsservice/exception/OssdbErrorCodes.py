# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds the error resources for ossdb tools service errors"""

from .OssdbErrorConstants import OssdbErrorConstants
from .OssdbErrorResource import OssdbErrorResource

class OssdbErrorCodes():
    
    """ AZURE MYSQL FLEXIBLE SERVER CONNECTION ERROR CODES """
    
    def MYSQL_FLEX_SSL_REQUIRED_NOT_PROVIDED(errmsg: str) :
        return OssdbErrorResource(
            OssdbErrorConstants.MYSQL_FLEX_SSL_REQUIRED_NOT_PROVIDED_CODE,
            errmsg,
            OssdbErrorConstants.MYSQL_FLEX_SSL_REQUIRED_NOT_PROVIDED_CAUSES,
            OssdbErrorConstants.MYSQL_FLEX_SSL_REQUIRED_NOT_PROVIDED_SUGGESTIONS
        )
        
    def MYSQL_FLEX_IP_NOT_WHITELISTED(errmsg: str) :
        return OssdbErrorResource(
            OssdbErrorConstants.MYSQL_FLEX_IP_NOT_WHITELISTED_CODE,
            errmsg,
            None,
            OssdbErrorConstants.MYSQL_FLEX_IP_NOT_WHITELISTED_SUGGESTIONS
        )
    
    def MYSQL_FLEX_INCORRECT_CREDENTIALS(errmsg: str) :
        return OssdbErrorResource(
            OssdbErrorConstants.MYSQL_FLEX_INCORRECT_CREDENTIALS_CODE,
            errmsg,
            OssdbErrorConstants.MYSQL_FLEX_INCORRECT_CREDENTIALS_CAUSES,
            OssdbErrorConstants.MYSQL_FLEX_INCORRECT_CREDENTIALS_SUGGESTIONS
        )