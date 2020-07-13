# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.language.query.pg_lightweight_metadata import PGLightweightMetadata
from ossdbtoolsservice.language.query.mysql_lightweight_metadata import MySQLLightweightMetadata

__all__ = ['PGLightweightMetadata', 'MySQLLightweightMetadata']
