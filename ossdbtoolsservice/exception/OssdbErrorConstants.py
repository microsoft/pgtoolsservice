# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds the error resource constants for ossdb tools service errors"""

class OssdbErrorConstants():
    
    """ ERROR CODES """
    MYSQL_FLEX_SSL_REQUIRED_NOT_PROVIDED_CODE = 50001
    MYSQL_FLEX_IP_NOT_WHITELISTED_CODE = 50002
    MYSQL_FLEX_INCORRECT_CREDENTIALS_CODE = 50003
    
    """ ERROR CAUSES """
    MYSQL_FLEX_SSL_REQUIRED_NOT_PROVIDED_CAUSES = "SSL required by server but not provided by client"
    MYSQL_FLEX_INCORRECT_CREDENTIALS_CAUSES = "Incorrect credentials provided"
    
    """ERROR SUGGESTIONS """
    MYSQL_FLEX_SSL_REQUIRED_NOT_PROVIDED_SUGGESTIONS = "Check that the ssl parameters are configured. \nhttps://docs.microsoft.com/en-us/azure/mysql/flexible-server/how-to-connect-tls-ssl"
    MYSQL_FLEX_IP_NOT_WHITELISTED_SUGGESTIONS = "Check that the firewall settings allow connections from the user's address."
    MYSQL_FLEX_INCORRECT_CREDENTIALS_SUGGESTIONS = "Check that the credentials(hostname, password, ssl cert) provided are correct"