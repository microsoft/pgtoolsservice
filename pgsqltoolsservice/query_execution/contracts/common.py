# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Contains contracts for query execution service"""

from datetime import datetime
import pgsqltoolsservice.utils as utils
from enum import Enum

DESC = {'name':0, 'type_code':1, 'display_size':2, 'internal_size':3, 'precision':4, 'scale':5, 'null_ok':6}

class QuerySelection(object):
    """Container class for a selection range from file"""

    @classmethod
    def from_data(cls, start_line: int, start_column: int, end_line: int, end_column: int):
        obj = QuerySelection()
        obj.start_line = start_line
        obj.start_column = start_column
        obj.end_line = end_line
        obj.end_column = end_column

    @classmethod
    def from_dict(cls, dictionary: dict):
        return utils.convert_from_dict(cls, dictionary)

    def __init__(self):
        self.start_line: int = 0
        self.start_column: int = 0
        self.end_line: int = 0
        self.end_column: int = 0

class SelectionData(object):    

        def __init__(self, start_line, start_column, end_line, end_column):
                """Constructs a SelectionData object"""
                self.start_line = start_line
                self.start_column = start_column
                self.end_line = end_line
                self.end_column = end_column

class BatchSummary(object):

    def __init__(self,
                 batchId: int,
                 selection: SelectionData = None,
                 execution_start: str = None,
                 has_error: bool = False):
        self.id = batchId
        self.selection = selection
        self.execution_start: str = execution_start
        self.has_error = has_error
        self.execution_end: str = None
        self.execution_elapsed = None
        self.result_set_summaries = None
        self.special_action = None
            


class ResultMessage(object):

    def __init__(self, batch_id, is_error, time, message):
        self.batch_id = batch_id
        self.is_error = is_error
        self.time = time
        self.message = message


class ResultSetSummary(object):

    def __init__(self, ident, batch_id, row_count, column_info, special_action):
        self.id = ident
        self.batch_id = batch_id
        self.row_count = row_count
        self.column_info = column_info
        self.special_action = special_action

class DbColumn(object):

    #The cursor_description is part of psycopg's cursor class' description property.
    #It is a property that is a tuple (read-only) containing sequences of 7-item sequences.
    #Each inner sequence item can be referenced by using DESC
    def __init__(self, column_ordinal, cursor_description):
        #TODO: Retrieve additional fields if necessary and relevant. Leaving as 'None' for now

        #Note that 'null_ok' is always 'None' by default because it's not easy to retrieve
        #Need to take a look if we should turn this on if it's important
        self.allow_db_null = cursor_description[DESC['null_ok']]
        self.base_catalog_name = None
        self.base_column_name = cursor_description[DESC['name']]
        self.base_schema_name = None
        self.base_server_name = None
        self.base_table_name = None
        self.column_ordinal = column_ordinal
        #From documentation, it seems like 'internal_size' is for the max size and
        #'display_size' is for the actual size based off of the largest entry in the column so far.
        # 'display_size' is always 'None' by default since it's expensive to calculate.
        # 'internal_size' is negative if column max is of a dynamic / variable size
        self.column_size = cursor_description[DESC['internal_size']]
        self.is_aliased = None
        self.is_auto_increment = None
        self.is_expression = None
        self.is_hidden = None
        self.is_identity = None
        self.is_key = None
        self.is_long = None
        self.is_read_only = None
        self.is_unique = None
        self.numeric_precision = cursor_description[DESC['precision']]
        self.numeric_scale = cursor_description[DESC['scale']]
        self.udt_assembly_qualified_name = cursor_description[DESC['null_ok']]
        self.data_type = None
        self.data_type_name = None
        self.is_bytes = None
        self.is_chars = None
        self.is_sql_variant = None
        self.is_udt = None
        self.is_xml = None
        self.is_json = None
        self.sql_db_type = None

class DbCellValue(object):

    def __init__(self, display_value, is_null, raw_object, row_id):
        self.display_value = display_value
        self.is_null = is_null
        self.raw_object = raw_object
        self.row_id = row_id

class BatchEventParams(object):

    def __init__(self, batch_summary, owner_uri):
        self.batch_summary = batch_summary
        self.owner_uri = owner_uri

class MessageParams(object):

    def __init__(self, message, owner_uri):
        self.message = message
        self.owner_uri = owner_uri

class QueryCompleteParams(object):

    def __init__(self, batch_summaries, owner_uri):
        self.batch_summaries = batch_summaries
        self.owner_uri = owner_uri
        
class ResultSetEventParams(object):

    def __init__(self, result_set_summary, owner_uri):
        self.result_set_summary = result_set_summary
        self.owner_uri = owner_uri

class ResultSetSubset(object):

    def __init__(self, row_count, rows):
        self.row_count = row_count
        self.rows = rows

class SubsetResult(object):
    
    def __init__(self, result_subset):
        self.result_subset = result_subset

class SpecialAction(object):

    def __init__(self):
        self.flags = 0


