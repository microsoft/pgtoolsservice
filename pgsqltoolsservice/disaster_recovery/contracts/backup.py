# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing contracts for backup operations"""

from typing import List  # noqa

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils


class DefaultDatabaseInfoParams:
    """Parameters for the requests that involve a database"""
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.owner_uri: str = None


class BackupParams:
    """Parameters for a backup request"""
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary, backup_info=BackupInfo)

    def __init__(self):
        self.owner_uri: str = None
        self.backup_info: BackupInfo = None
        self.is_scripting: bool = None


class BackupInfo:
    """Options for a requested backup"""
    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.serialization.convert_from_dict(cls, dictionary, ignore_extra_attributes=True)

    def __init__(self):
        self.owner_uri: str = None
        self.database_name: str = None
        self.backup_path_list: List[str] = None


BACKUP_CONFIG_INFO_REQUEST = IncomingMessageConfiguration('disasterrecovery/backupconfiginfo', DefaultDatabaseInfoParams)
BACKUP_REQUEST = IncomingMessageConfiguration('disasterrecovery/backup', BackupParams)
