# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing contracts for backup operations"""

import enum
from typing import List  # noqa

from pgsqltoolsservice.hosting import IncomingMessageConfiguration
import pgsqltoolsservice.utils as utils


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
        return utils.serialization.convert_from_dict(cls, dictionary, ignore_extra_attributes=True, type=BackupType)

    def __init__(self):
        self.type: BackupType = None
        self.path: str = None
        self.jobs: int = None
        self.compress: int = None
        self.data_only: bool = None
        self.blobs: bool = None
        self.clean: bool = None
        self.create: bool = None
        self.encoding: str = None
        self.schema: str = None
        self.exclude_schema: str = None
        self.oids: bool = None
        self.no_owner: bool = None
        self.schema_only: bool = None
        self.superuser: str = None
        self.table: str = None
        self.exclude_table: str = None
        self.no_privileges: bool = None
        self.column_inserts: bool = None
        self.disable_dollar_quoting: bool = None
        self.disable_triggers: bool = None
        self.enable_row_security: bool = None
        self.exclude_table_data: str = None
        self.if_exists: bool = None
        self.inserts: bool = None
        self.no_security_labels: bool = None
        self.no_synchronized_snapshots: bool = None
        self.no_tablespaces: bool = None
        self.no_unlogged_table_data: bool = None
        self.quote_all_identifiers: bool = None
        self.section: str = None
        self.serializable_deferrable: bool = None
        self.snapshot: str = None
        self.strict_names: bool = None
        self.use_set_session_authorization: bool = None


class BackupType(enum.Enum):
    """Enum for the type of backups that are supported"""
    PG_DUMP = 'dump'
    DIRECTORY = 'directory'
    TAR = 'tar'
    PLAIN_TEXT = 'sql'


BACKUP_REQUEST = IncomingMessageConfiguration('disasterrecovery/backup', BackupParams)
