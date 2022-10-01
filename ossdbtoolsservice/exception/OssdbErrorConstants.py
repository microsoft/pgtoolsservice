# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""This module holds the error resource constants for ossdb tools service errors"""

class OssdbErrorConstants():

    """ ERROR MESSAGES """
    MYSQL_SSL_CA_REQUIRED_FOR_VERIFY_MODES_ERRMSG = "SSL Connection Error: SSL CA certificate is required if ssl-mode is VERIFY_CA or VERIFY_IDENTITY."

    """ INTERNAL ERROR CODES """
    MYSQL_FLEX_SSL_REQUIRED_NOT_PROVIDED_CODE = 50001
    MYSQL_FLEX_IP_NOT_WHITELISTED_CODE = 50002
    MYSQL_FLEX_INCORRECT_CREDENTIALS_CODE = 50003
    MYSQL_SSL_CA_REQUIRED_FOR_VERIFY_MODES_CODE = 50004

    """ ERROR CAUSES """
    MYSQL_FLEX_SSL_REQUIRED_NOT_PROVIDED_CAUSES = "SSL encryption is required by server but is not configured by client."
    MYSQL_FLEX_INCORRECT_CREDENTIALS_CAUSES = "The credentials provided are invalid."

    """ERROR SUGGESTIONS """
    MYSQL_FLEX_SSL_REQUIRED_NOT_PROVIDED_SUGGESTIONS = "Navigate to \'Advanced Properties\' tab and check that the SSL parameters are correctly configured. \nFor more details on connecting to Azure Database for MySQL using SSL encryptions, see https://learn.microsoft.com/azure/mysql/flexible-server/how-to-connect-tls-ssl"
    MYSQL_FLEX_IP_NOT_WHITELISTED_SUGGESTIONS = "Verify and configure the firewall settings on your Azure Database for MySQL flexible server to allow connections from the your client address. \n For more details, see https://learn.microsoft.com/azure/mysql/flexible-server/how-to-manage-firewall-portal"
    MYSQL_FLEX_INCORRECT_CREDENTIALS_SUGGESTIONS = "Check that the provided credentials (Server name, User name, Password, SSL cert) are correct."
    MYSQL_SSL_CA_REQUIRED_FOR_VERIFY_MODES_SUGGESTIONS = "To connect using these SSL modes, navigate to \'Advanced Properties\' tab and configure the SSL CA certificate. \nFor more details on SSL modes, see https://dev.mysql.com/doc/refman/8.0/en/using-encrypted-connections.html"