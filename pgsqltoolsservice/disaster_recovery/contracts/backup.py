# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing contracts for backup operations"""

import enum
from typing import List  # noqa

from pgsqltoolsservice.capabilities.contracts import CategoryValue, FeatureMetadataProvider, ServiceOption
from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.serialization import Serializable


class BackupParams(Serializable):
    """Parameters for a backup request"""
    @classmethod
    def get_child_serializable_types(cls):
        return {'backup_info': BackupInfo}

    def __init__(self):
        self.owner_uri: str = None
        self.backup_info: BackupInfo = None
        self.task_execution_mode = None


class BackupInfo(Serializable):
    """Options for a requested backup"""
    @classmethod
    def get_child_serializable_types(cls):
        return {'type': BackupType}

    @classmethod
    def ignore_extra_attributes(cls):
        return True

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


# These options are handled in the disaster recovery service's _perform_backup method. A few have special case handling, but most are handled automatically by
# using the option's name as the flag name, and the setting as the value. The BackupInfo contract above has a field corresponding to each option.
# TODO: Localize the display names and descriptions
BACKUP_OPTIONS = FeatureMetadataProvider(
    True,
    'backup',
    [
        ServiceOption(
            name='type',
            display_name='Backup type',
            description='The type of backup to perform',
            value_type=ServiceOption.VALUE_TYPE_CATEGORY,
            is_required=True,
            category_values=[
                CategoryValue(
                    display_name='pg_dump/pg_restore (.dump)',
                    name='dump'
                ),
                CategoryValue(
                    display_name='Directory',
                    name='directory'
                ),
                CategoryValue(
                    display_name='Archive (.tar)',
                    name='tar'
                ),
                CategoryValue(
                    display_name='Plain text (.sql)',
                    name='sql'
                ),
            ],
            default_value='sql'
        ),
        ServiceOption(
            name='path',
            display_name='Output path',
            description='The path to the backup file/directory that will be produced',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=True
        ),
        ServiceOption(
            name='jobs',
            display_name='Number of jobs',
            description='The number of parallel jobs to use for the dump',
            value_type=ServiceOption.VALUE_TYPE_NUMBER,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='compress',
            display_name='Compression level',
            description='The compression level (for compressed formats)',
            value_type=ServiceOption.VALUE_TYPE_CATEGORY,
            is_required=False,
            group_name='Advanced',
            category_values=[CategoryValue('0', '0'), CategoryValue('1', '1'), CategoryValue('2', '2'), CategoryValue('3', '3'), CategoryValue('4', '4'),
                             CategoryValue('5', '5'), CategoryValue('6', '6'), CategoryValue('7', '7'), CategoryValue('8', '8'), CategoryValue('9', '9')]
        ),
        ServiceOption(
            name='dataOnly',
            display_name='Data only',
            description='Dump only the data, not the schema',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='blobs',
            display_name='Blobs',
            description='Include large objects in dump',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='clean',
            display_name='Clean',
            description='Clean (drop) database objects before recreating',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='create',
            display_name='Create',
            description='Include commands to create database in dump',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='encoding',
            display_name='Encoding',
            description='Dump the data in the given encoding',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='schema',
            display_name='Schema',
            description='Dump the named schema(s) only',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='excludeSchema',
            display_name='Exclude schema',
            description='Do not dump the named schema(s)',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='oids',
            display_name='OIDs',
            description='Include OIDs in the dump',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noOwner',
            display_name='No owner',
            description='Skip restoration of object ownership in plain-text format',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='schemaOnly',
            display_name='Schema only',
            description='Dump only the schema, no data',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='superuser',
            display_name='Superuser',
            description='Superuser user name to use in plain-text format',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='table',
            display_name='Table',
            description='Dump the named table(s) only',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='excludeTable',
            display_name='Exclude table',
            description='Do not dump the named table(s)',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noPrivileges',
            display_name='No privileges',
            description='Do not dump privileges (grant/revoke)',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='columnInserts',
            display_name='Column inserts',
            description='Dump data as INSERT commands with column names',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='disableDollarQuoting',
            display_name='Disable dollar quoting',
            description='Disable dollar quoting; use SQL standard quoting',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='disableTriggers',
            display_name='Disable triggers',
            description='Disable triggers during data-only restore',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='enable_row_security',
            display_name='Enable row security',
            description='Dump only content user has access to',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='excludeDataTable',
            display_name='Exclude data table',
            description='Do not dump data for the named table(s)',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='ifExists',
            display_name='Use IF EXISTS',
            description='Use IF EXISTS when dropping objects',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='inserts',
            display_name='Inserts',
            description='Dump data as INSERT commands, rather than COPY',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noSecurityLabels',
            display_name='No security labels',
            description='Do not dump security label assignments',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noSynchronizedSnapshots',
            display_name='No synchronized snapshots',
            description='Do not use synchronized snapshots in parallel jobs',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noTablespaces',
            display_name='No tablespaces',
            description='Do not dump tablespace assignments',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noUnloggedTableData',
            display_name='No unlogged table data',
            description='Do not dump unlogged table data',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='quoteAllIidentifiers',
            display_name='Quote all identifiers',
            description='Quote all identifiers, even if not key words',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='section',
            display_name='Section',
            description='Dump named section (pre-data, data, or post-data)',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='serializableDeferrable',
            display_name='Serializable deferrable',
            description='Wait until the dump can run without anomalies',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='snapshot',
            display_name='Snapshot',
            description='Use given snapshot for the dump',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='strictNames',
            display_name='Strict names',
            description='Require table and/or schema include patterns to match at least one entity each',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='useSetSessionAuthorization',
            display_name='Use SET SESSION AUTHORIZATION',
            description='Use SET SESSION AUTHORIZATION commands instead of ALTER OWNER commands to set ownership',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        )])
