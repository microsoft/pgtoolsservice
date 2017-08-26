# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Module containing contracts for restore operations"""

from pgsqltoolsservice.capabilities.contracts import FeatureMetadataProvider, ServiceOption
from pgsqltoolsservice.hosting import IncomingMessageConfiguration
from pgsqltoolsservice.serialization import Serializable


class RestoreParams(Serializable):
    """Parameters for a restore request"""
    @classmethod
    def get_child_serializable_types(cls):
        return {'options': RestoreOptions}

    def __init__(self):
        self.owner_uri: str = None
        self.options: RestoreOptions = None
        self.task_execution_mode = None


class RestoreOptions(Serializable):
    """Options for a requested restore"""
    @classmethod
    def ignore_extra_attributes(cls):
        return True

    def __init__(self):
        self.path: str = None
        self.data_only: bool = None
        self.clean: bool = None
        self.create: bool = None
        self.exit_on_error: bool = None
        self.index: str = None
        self.jobs: int = None
        self.use_list: str = None
        self.schema: str = None
        self.no_owner: bool = None
        self.function: str = None
        self.schema_only: bool = None
        self.superuser: str = None
        self.table: str = None
        self.trigger: str = None
        self.no_privileges: bool = None
        self.single_transaction: bool = None
        self.disable_triggers: bool = None
        self.enable_row_security: bool = None
        self.if_exists: bool = None
        self.no_data_for_failed_tables: bool = None
        self.no_security_labels: bool = None
        self.no_tablespaces: bool = None
        self.section: str = None
        self.strict_names: bool = None
        self.role: str = None


RESTORE_REQUEST = IncomingMessageConfiguration('disasterrecovery/restore', RestoreParams)

# These options are handled in the disaster recovery service's _perform_restore method. The path has special case handling, but most are handled automatically
# by using the option's name as the flag name, and the setting as the value. The RestoreOptions contract above has a field corresponding to each option.
# TODO: Localize the display names and descriptions
RESTORE_OPTIONS = FeatureMetadataProvider(
    True,
    'Restore',
    [
        ServiceOption(
            name='path',
            display_name='Backup path',
            description='The path to the backup file/directory to be used for restore',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=True
        ),
        ServiceOption(
            name='dataOnly',
            display_name='Data only',
            description='Restore only the data, not the schema',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='clean',
            display_name='Clean',
            description='Drop database objects before recreating',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='create',
            display_name='Create',
            description='Create the target database',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='exitOnError',
            display_name='Exit on error',
            description='Exit on error (default is to continue)',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='index',
            display_name='Index',
            description='Restore named index',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='jobs',
            display_name='Number of jobs',
            description='The number of parallel jobs to use for the restore',
            value_type=ServiceOption.VALUE_TYPE_NUMBER,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='useList',
            display_name='Use list filename',
            description='Use table of contents from the given file for selecting/ordering output',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='schema',
            display_name='Schema',
            description='Restore only objects in the given schema',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noOwner',
            display_name='No owner',
            description='Skip restoration of object ownership',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='function',
            display_name='Function',
            description='Restore named function',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='schemaOnly',
            display_name='Schema only',
            description='Restore only the schema, not data',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='superuser',
            display_name='Superuser name',
            description='Superuser name to use for disabling triggers',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='table',
            display_name='Table',
            description='Restore named relation',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='trigger',
            display_name='Trigger',
            description='Restore named trigger',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noPrivileges',
            display_name='No privileges',
            description='Skip restoration of access privileges (grant/revoke)',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='singleTransaction',
            display_name='Single transaction',
            description='Restore as a single transaction',
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
            name='enableRowSecurity',
            display_name='Enable row security',
            description='Enable row security',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
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
            name='noDataForFailedTables',
            display_name='No data for failed tables',
            description='Do not restore data of tables that could not be created',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noSecurityLabels',
            display_name='No security labels',
            description='Do not restore security labels',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='noTablespaces',
            display_name='No tablespaces',
            description='Do not restore tablespace assignments',
            value_type=ServiceOption.VALUE_TYPE_BOOLEAN,
            is_required=False,
            group_name='Advanced'
        ),
        ServiceOption(
            name='section',
            display_name='Section',
            description='Restore named section (pre-data, data, or post-data)',
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
            name='role',
            display_name='Role name',
            description='Do SET ROLE to the given role name before restore',
            value_type=ServiceOption.VALUE_TYPE_STRING,
            is_required=False,
            group_name='Advanced'
        )
    ])
