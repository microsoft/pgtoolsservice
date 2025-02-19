# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing contracts for backup operations"""

import enum

# Avoid name conflict with BackupInfo.type
from typing import Type  # noqa: UP035

from ossdbtoolsservice.capabilities.contracts import (
    CategoryValue,
    FeatureMetadataProvider,
    ServiceOption,
)
from ossdbtoolsservice.hosting import IncomingMessageConfiguration
from ossdbtoolsservice.serialization import Serializable


class BackupType(enum.Enum):
    """Enum for the type of backups that are supported"""

    PG_DUMP = "dump"
    DIRECTORY = "directory"
    TAR = "tar"
    PLAIN_TEXT = "sql"


class BackupInfo(Serializable):
    """Options for a requested backup"""

    type: BackupType | None
    path: str | None
    jobs: int | None
    compress: int | None
    data_only: bool | None
    blobs: bool | None
    clean: bool | None
    create: bool | None
    encoding: str | None
    schema: str | None
    exclude_schema: str | None
    oids: bool | None
    no_owner: bool | None
    schema_only: bool | None
    superuser: str | None
    table: str | None
    exclude_table: str | None
    no_privileges: bool | None
    column_inserts: bool | None
    disable_dollar_quoting: bool | None
    disable_triggers: bool | None
    enable_row_security: bool | None
    exclude_table_data: str | None
    if_exists: bool | None
    inserts: bool | None
    no_security_labels: bool | None
    no_synchronized_snapshots: bool | None
    no_tablespaces: bool | None
    no_unlogged_table_data: bool | None
    quote_all_identifiers: bool | None
    section: str | None
    serializable_deferrable: bool | None
    snapshot: str | None
    strict_names: bool | None
    use_set_session_authorization: bool | None

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, Type[BackupType]]:  # noqa: UP006
        return {"type": BackupType}

    @classmethod
    def ignore_extra_attributes(cls) -> bool:
        return True

    def __init__(self) -> None:
        self.type = None
        self.path = None
        self.jobs = None
        self.compress = None
        self.data_only = None
        self.blobs = None
        self.clean = None
        self.create = None
        self.encoding = None
        self.schema = None
        self.exclude_schema = None
        self.oids = None
        self.no_owner = None
        self.schema_only = None
        self.superuser = None
        self.table = None
        self.exclude_table = None
        self.no_privileges = None
        self.column_inserts = None
        self.disable_dollar_quoting = None
        self.disable_triggers = None
        self.enable_row_security = None
        self.exclude_table_data = None
        self.if_exists = None
        self.inserts = None
        self.no_security_labels = None
        self.no_synchronized_snapshots = None
        self.no_tablespaces = None
        self.no_unlogged_table_data = None
        self.quote_all_identifiers = None
        self.section = None
        self.serializable_deferrable = None
        self.snapshot = None
        self.strict_names = None
        self.use_set_session_authorization = None


class BackupParams(Serializable):
    """Parameters for a backup request"""

    owner_uri: str | None
    backup_info: BackupInfo | None
    task_execution_mode: str | None

    @classmethod
    def get_child_serializable_types(cls) -> dict[str, type[BackupInfo]]:
        return {"backup_info": BackupInfo}

    def __init__(self) -> None:
        self.owner_uri = None
        self.backup_info = None
        self.task_execution_mode = None


BACKUP_REQUEST = IncomingMessageConfiguration("backup/backup", BackupParams)


# These options are handled in the disaster recovery service's _perform_backup method.
# A few have special case handling, but most are handled automatically by
# using the option's name as the flag name, and the setting as the value.
# The BackupInfo contract above has a field corresponding to each option.
# TODO: Localize the display names and descriptions
BACKUP_OPTIONS = FeatureMetadataProvider(
    True,
    "backup",
    [
        ServiceOption(
            name="type",
            display_name="Backup type",
            description="The type of backup to perform",
            value_type=ServiceOption.VALUE_TYPE_CATEGORY,
            is_required=True,
            category_values=[
                CategoryValue(display_name="pg_dump/pg_restore (.dump)", name="dump"),
                CategoryValue(display_name="Directory", name="directory"),
                CategoryValue(display_name="Archive (.tar)", name="tar"),
                CategoryValue(display_name="Plain text (.sql)", name="sql"),
            ],
            default_value="sql",
        ),
        ServiceOption(
            name="path",
            display_name="Output path",
            description="The path to the backup file/directory that will be produced",
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=True,
        ),
        ServiceOption(
            name="jobs",
            display_name="Number of jobs",
            description="The number of parallel jobs to use for the dump",
            value_type=ServiceOption.VALUE_TYPE_NUMBER,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="compress",
            display_name="Compression level",
            description="The compression level (for compressed formats)",
            value_type=ServiceOption.VALUE_TYPE_CATEGORY,
            is_required=False,
            group_name="Advanced",
            category_values=[
                CategoryValue("0", "0"),
                CategoryValue("1", "1"),
                CategoryValue("2", "2"),
                CategoryValue("3", "3"),
                CategoryValue("4", "4"),
                CategoryValue("5", "5"),
                CategoryValue("6", "6"),
                CategoryValue("7", "7"),
                CategoryValue("8", "8"),
                CategoryValue("9", "9"),
            ],
        ),
        ServiceOption(
            name="dataOnly",
            display_name="Data only",
            description="Dump only the data, not the schema",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="blobs",
            display_name="Blobs",
            description="Include large objects in dump",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="clean",
            display_name="Clean",
            description="Clean (drop) database objects before recreating",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="create",
            display_name="Create",
            description="Include commands to create database in dump",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="encoding",
            display_name="Encoding",
            description="Dump the data in the given encoding",
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="schema",
            display_name="Schema",
            description="Dump the named schema(s) only",
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="excludeSchema",
            display_name="Exclude schema",
            description="Do not dump the named schema(s)",
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="oids",
            display_name="OIDs",
            description="Include OIDs in the dump",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="noOwner",
            display_name="No owner",
            description="Skip restoration of object ownership in plain-text format",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="schemaOnly",
            display_name="Schema only",
            description="Dump only the schema, no data",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="superuser",
            display_name="Superuser",
            description="Superuser user name to use in plain-text format",
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="table",
            display_name="Table",
            description="Dump the named table(s) only",
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="excludeTable",
            display_name="Exclude table",
            description="Do not dump the named table(s)",
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="noPrivileges",
            display_name="No privileges",
            description="Do not dump privileges (grant/revoke)",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="columnInserts",
            display_name="Column inserts",
            description="Dump data as INSERT commands with column names",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="disableDollarQuoting",
            display_name="Disable dollar quoting",
            description="Disable dollar quoting; use SQL standard quoting",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="disableTriggers",
            display_name="Disable triggers",
            description="Disable triggers during data-only restore",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="enable_row_security",
            display_name="Enable row security",
            description="Dump only content user has access to",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="excludeDataTable",
            display_name="Exclude data table",
            description="Do not dump data for the named table(s)",
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="ifExists",
            display_name="Use IF EXISTS",
            description="Use IF EXISTS when dropping objects",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="inserts",
            display_name="Inserts",
            description="Dump data as INSERT commands, rather than COPY",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="noSecurityLabels",
            display_name="No security labels",
            description="Do not dump security label assignments",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="noSynchronizedSnapshots",
            display_name="No synchronized snapshots",
            description="Do not use synchronized snapshots in parallel jobs",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="noTablespaces",
            display_name="No tablespaces",
            description="Do not dump tablespace assignments",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="noUnloggedTableData",
            display_name="No unlogged table data",
            description="Do not dump unlogged table data",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="quoteAllIidentifiers",
            display_name="Quote all identifiers",
            description="Quote all identifiers, even if not key words",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="section",
            display_name="Section",
            description="Dump named section (pre-data, data, or post-data)",
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="serializableDeferrable",
            display_name="Serializable deferrable",
            description="Wait until the dump can run without anomalies",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="snapshot",
            display_name="Snapshot",
            description="Use given snapshot for the dump",
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="strictNames",
            display_name="Strict names",
            description="Require table and/or schema include patterns "
            "to match at least one entity each",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
        ServiceOption(
            name="useSetSessionAuthorization",
            display_name="Use SET SESSION AUTHORIZATION",
            description="Use SET SESSION AUTHORIZATION commands instead of "
            "ALTER OWNER commands to set ownership",
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name="Advanced",
        ),
    ],
)
