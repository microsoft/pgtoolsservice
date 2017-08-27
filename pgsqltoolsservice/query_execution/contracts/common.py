# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Contains contracts for query execution service"""
from typing import List, Dict  # noqa

from pgsqltoolsservice.workspace.contracts import Position, Range
from pgsqltoolsservice.serialization import Serializable
import pgsqltoolsservice.utils as utils

DESC = {'name': 0, 'type_code': 1, 'display_size': 2, 'internal_size': 3, 'precision': 4, 'scale': 5, 'null_ok': 6}


class SelectionData(Serializable):
    """Container class for a selection range from file"""

    def __init__(self, start_line: int = 0, start_column: int = 0, end_line: int = 0, end_column: int = 0):
        self.start_line: int = start_line
        self.start_column: int = start_column
        self.end_line: int = end_line
        self.end_column: int = end_column

    def to_range(self):
        """Convert the SelectionData object to a workspace service Range object"""
        return Range(Position(self.start_line, self.start_column), Position(self.end_line, self.end_column))


class BatchSummary:

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


class ResultMessage:

    def __init__(self, batch_id: int, is_error: bool, time, message: str):
        self.batch_id: int = batch_id
        self.is_error: bool = is_error
        self.time = time
        self.message: str = message


class ResultSetSummary:

    def __init__(self, ident, batch_id, row_count, column_info, special_action):
        self.id = ident
        self.batch_id = batch_id
        self.row_count = row_count
        self.column_info = column_info
        self.special_action = special_action


class DbColumn:

    def __init__(self):
        self.allow_db_null: bool = None
        self.base_catalog_name: str = None
        self.column_size: int = None
        self.numeric_precision: int = None
        self.numeric_scale: int = None
        self.base_schema_name: str = None
        self.base_server_name: str = None
        self.base_table_name: str = None
        self.column_ordinal: int = None
        self.base_column_name: str = None
        self.column_name: str = None
        self.is_aliased: bool = None
        self.is_auto_increment: bool = None
        self.is_expression: bool = None
        self.is_hidden: bool = None
        self.is_identity: bool = None
        self.is_key: bool = None
        self.is_long: bool = None
        self.is_read_only: bool = None
        self.is_unique: bool = None
        self.data_type = None
        self.data_type_name: str = None
        self.is_bytes: bool = None
        self.is_chars: bool = None
        self.is_sql_variant: bool = None
        self.is_udt: bool = None
        self.is_xml: bool = None
        self.is_json: bool = None

    @property
    def is_updatable(self):
        # TBD- Implementation Pending. This is not used anywhere currently
        return True

    # The cursor_description is an element from psycopg's cursor class' description property.
    # It is a property that is a tuple (read-only) containing a 7-item sequence.
    # Each inner sequence item can be referenced by using DESC
    @classmethod
    def from_cursor_description(cls, column_ordinal: int, cursor_description: tuple):

        instance = cls()

        # Note that 'null_ok' is always 'None' by default because it's not easy to retrieve
        # Need to take a look if we should turn this on if it's important
        instance.allow_db_null: bool = cursor_description[DESC['null_ok']]
        instance.base_column_name: str = cursor_description[DESC['name']]
        instance.column_name: str = cursor_description[DESC['name']]

        # From documentation, it seems like 'internal_size' is for the max size and
        # 'display_size' is for the actual size based off of the largest entry in the column so far.
        # 'display_size' is always 'None' by default since it's expensive to calculate.
        # 'internal_size' is negative if column max is of a dynamic / variable size

        instance.column_size: int = cursor_description[DESC['internal_size']]
        instance.numeric_precision: int = cursor_description[DESC['precision']]
        instance.numeric_scale: int = cursor_description[DESC['scale']]
        instance.column_ordinal: int = column_ordinal

        return instance


class DbCellValue:

    def __init__(self, display_value: any, is_null: bool, raw_object: object, row_id: int):
        self.display_value: str = None if (display_value is None) else str(display_value)
        self.is_null: bool = is_null
        self.row_id: int = row_id
        self.raw_object = raw_object


class ResultSetSubset:

    def __init__(self, results, owner_uri: str, batch_ordinal: int,
                 result_set_ordinal: int, start_index: int, end_index: int):
        self.rows: List[List[DbCellValue]] = self.build_db_cell_values(
            results, owner_uri, batch_ordinal, result_set_ordinal, start_index, end_index)
        self.row_count: int = len(self.rows)

    def build_db_cell_values(self, results, owner_uri: str, batch_ordinal: int,
                             result_set_ordinal: int, start_index: int,
                             end_index: int) -> List[List[DbCellValue]]:
        """ param results: a list of rows for a query result, where each row consists of tuples
        :param results: mapping of owner uris to their list of batches Dict[str, List[Batch]]
        :param batch_ordinal: ordinal of the batch within 'results'
        :param result_set_ordinal: ordinal of the result set within the batch's result_set field
        :param start_index: the starting index that we will index into a list of rows with, inclusive
        :param end_index: the ending index we will index into a list of rows with, exclusive
        """

        utils.validate.is_not_none("results", results)
        utils.validate.is_not_none("owner_uri", owner_uri)
        utils.validate.is_not_none("batch_ordinal", batch_ordinal)
        utils.validate.is_not_none("result_set_ordinal", result_set_ordinal)
        utils.validate.is_not_none("start_index", start_index)
        utils.validate.is_not_none("end_index", end_index)

        # Check the specified owner uri key exists
        if owner_uri not in results:
            raise IndexError(f'(Results corresponding to {owner_uri} do not exist)')  # TODO: Localize

        # Check that the list of batches for the specified owner uri exists
        utils.validate.is_not_none("results[owner_uri]", results[owner_uri])
        query = results[owner_uri]

        # validate that there is an entry for the batch at position batch_ordinal
        utils.validate.is_within_range("batch_ordinal", batch_ordinal, 0, len(query.batches) - 1)

        batch = query.batches[batch_ordinal]
        utils.validate.is_not_none("batch", batch)
        utils.validate.is_within_range("result_set_ordinal", result_set_ordinal, 0, 0)

        result_set = batch.result_set
        utils.validate.is_within_range("start_index", start_index, 0, end_index - 1)
        utils.validate.is_within_range("end_index", end_index - 1, start_index, len(result_set.rows) - 1)

        rows_list: List[List[DbCellValue]] = []
        row_id = start_index

        # operate only on results within the specified range
        for row_id in range(start_index, end_index):
            db_cell_value_row: List[DbCellValue] = [
                DbCellValue(
                    cell,
                    cell is None,
                    cell,
                    row_id) for cell in result_set.rows[row_id]]
            # Add our row to the overall row list
            rows_list.append(db_cell_value_row)
        return rows_list


class SubsetResult:

    def __init__(self, result_subset: ResultSetSubset):
        self.result_subset: ResultSetSubset = result_subset


class SpecialAction:

    def __init__(self):
        self.flags = 0


class QueryCancelResult:
    """Parameters to return as the result of a query dispose request"""

    def __init__(self, messages: str = None):
        # Optional error messages during query cancellation that can be sent back
        # Set to none if no errors
        self.messages = messages
