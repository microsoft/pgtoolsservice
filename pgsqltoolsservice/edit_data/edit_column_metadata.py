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
