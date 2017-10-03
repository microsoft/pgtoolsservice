# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from typing import Dict, List  # noqa

from pgsqltoolsservice.query.contracts import DbCellValue
import pgsqltoolsservice.utils as utils


class ResultSetSubset:

    @classmethod
    def from_result_set(cls, result_set, start_index: int, end_index: int):
        ''' Retrieves ResultSetSubset from Result set '''
        instance = cls()
        rows = cls._construct_rows(result_set, start_index, end_index)
        instance.rows = rows
        instance.row_count = len(rows)

        return instance

    @classmethod
    def from_query_results(cls, results, owner_uri: str, batch_ordinal: int,
                           result_set_ordinal: int, start_index: int, end_index: int):
        ''' Retrieves ResultSetSubset from Query results '''
        instance = cls()
        instance.rows: List[List[DbCellValue]] = instance.build_db_cell_values(
            results, owner_uri, batch_ordinal, result_set_ordinal, start_index, end_index)
        instance.row_count: int = len(instance.rows)

        return instance

    def __init__(self):
        self.rows: List[List[DbCellValue]] = []
        self.row_count: int = 0

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

        return ResultSetSubset._construct_rows(result_set, start_index, end_index)

    @staticmethod
    def _construct_rows(result_set, start_index: int, end_index: int):

        rows_list: List[List[DbCellValue]] = []
        row_id = start_index

        # operate only on results within the specified range
        for row_id in range(start_index, end_index):
            db_cell_value_row: List[DbCellValue] = [
                DbCellValue(
                    cell,
                    cell is None,
                    cell,
                    row_id) for cell in ResultSetSubset._get_row(result_set, row_id)]
            # Add our row to the overall row list
            rows_list.append(db_cell_value_row)
        return rows_list

    @staticmethod
    def _get_row(result_set, index):
        ''' This private method returns a row tuple
        in case a row is found within the index and returns empty
        tuple in case the index is greater than available
        '''

        if index < len(result_set.rows):
            return result_set.rows[index]
        return (None,) * len(result_set.columns_info)


class SubsetResult:

    def __init__(self, result_subset: ResultSetSubset):
        self.result_subset: ResultSetSubset = result_subset
