# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from pgsqltoolsservice.query_execution.contracts.common import DbColumn


class EditColumnMetadata:

    def __init__(self):
        self.default_value = None
        self.escaped_name = None
        self.has_extended_properties = False
        self.ordinal = None
        self.is_computed = False
        self.is_deterministic = False
        self.is_identity = False
        self.db_column: DbColumn = None
        self.is_calculated = None
        self.is_key = None
        self.is_trustworthy_for_uniqueness = None

    def extend(self, db_column: DbColumn):
        # Extend additional information from the SMO
        self.db_column = db_column
        self.is_trustworthy_for_uniqueness = db_column.is_unique or db_column.is_read_only is False or db_column.is_auto_increment
        self.is_key = db_column.is_key
        self.is_calculated = db_column.is_auto_increment is True or db_column.is_updatable is False
        self.has_extended_properties = True
