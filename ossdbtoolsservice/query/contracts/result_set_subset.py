# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from typing import TYPE_CHECKING

from ossdbtoolsservice.hosting import OutgoingMessageRegistration
from ossdbtoolsservice.query.contracts import DbCellValue
from ossdbtoolsservice.utils import validate

if TYPE_CHECKING:
    from ossdbtoolsservice.query.query import Query
    from ossdbtoolsservice.query.result_set import ResultSet


class ResultSetSubset:
    rows: list[list[DbCellValue]]
    row_count: int

    @classmethod
    def from_result_set(
        cls, result_set: "ResultSet", start_index: int, end_index: int
    ) -> "ResultSetSubset":
        """Retrieves ResultSetSubset from Result set"""
        instance = cls()
        rows = cls._construct_rows(result_set, start_index, end_index)
        instance.rows = rows
        instance.row_count = len(rows)

        return instance

    @classmethod
    def from_query_results(
        cls,
        results: dict[str, "Query"],
        owner_uri: str,
        batch_ordinal: int,
        result_set_ordinal: int,
        start_index: int,
        end_index: int,
    ) -> "ResultSetSubset":
        """Retrieves ResultSetSubset from Query results"""
        instance = cls()
        instance.rows = instance.build_db_cell_values(
            results, owner_uri, batch_ordinal, result_set_ordinal, start_index, end_index
        )
        instance.row_count = len(instance.rows)

        return instance

    def __init__(self) -> None:
        self.rows: list[list[DbCellValue]] = []
        self.row_count: int = 0

    def build_db_cell_values(
        self,
        results: dict[str, "Query"],
        owner_uri: str,
        batch_ordinal: int,
        result_set_ordinal: int,
        start_index: int,
        end_index: int,
    ) -> list[list[DbCellValue]]:
        """param results: a list of rows for a query result, where each row consists of tuples
        :param results: mapping of owner uris to their list of batches Dict[str, List[Batch]]
        :param batch_ordinal: ordinal of the batch within 'results'
        :param result_set_ordinal: ordinal of the result set within
            the batch's result_set field
        :param start_index: the starting index that we will index
            into a list of rows with, inclusive
        :param end_index: the ending index we will index into a list of rows with, exclusive
        """

        validate.is_not_none("results", results)
        validate.is_not_none("owner_uri", owner_uri)
        validate.is_not_none("batch_ordinal", batch_ordinal)
        validate.is_not_none("result_set_ordinal", result_set_ordinal)
        validate.is_not_none("start_index", start_index)
        validate.is_not_none("end_index", end_index)

        # Check the specified owner uri key exists
        if owner_uri not in results:
            raise IndexError(
                f"(Results corresponding to {owner_uri} do not exist)"
            )  # TODO: Localize

        # Check that the list of batches for the specified owner uri exists
        validate.is_not_none("results[owner_uri]", results[owner_uri])
        query = results[owner_uri]

        # validate that there is an entry for the batch at position batch_ordinal
        validate.is_within_range("batch_ordinal", batch_ordinal, 0, len(query.batches) - 1)

        batch = query.batches[batch_ordinal]
        validate.is_not_none("batch", batch)
        validate.is_within_range("result_set_ordinal", result_set_ordinal, 0, 0)

        result_set = batch.result_set

        if result_set is None:
            raise ValueError(f"Result set for batch {batch_ordinal} does not exist")

        validate.is_within_range("start_index", start_index, 0, end_index - 1)
        validate.is_within_range(
            "end_index", end_index - 1, start_index, result_set.row_count - 1
        )

        return ResultSetSubset._construct_rows(result_set, start_index, end_index)

    @staticmethod
    def _construct_rows(
        result_set: "ResultSet", start_index: int, end_index: int
    ) -> list[list[DbCellValue]]:
        rows_list: list[list[DbCellValue]] = []
        row_id = start_index

        # operate only on results within the specified range
        for row_id in range(start_index, end_index):
            db_cell_value_row: list[DbCellValue] = ResultSetSubset._get_row(
                result_set, row_id
            )
            # Add our row to the overall row list
            rows_list.append(db_cell_value_row)
        return rows_list

    @staticmethod
    def _get_row(result_set: "ResultSet", index: int) -> list[DbCellValue]:
        """This private method returns a row tuple
        in case a row is found within the index and returns empty
        tuple in case the index is greater than available
        """

        if index < result_set.row_count:
            return result_set.get_row(index)
        return [DbCellValue(None, True, None, index)] * len(result_set.columns_info)


class SubsetResult:
    result_subset: ResultSetSubset

    def __init__(self, result_subset: ResultSetSubset):
        self.result_subset: ResultSetSubset = result_subset


OutgoingMessageRegistration.register_outgoing_message(SubsetResult)
OutgoingMessageRegistration.register_outgoing_message(ResultSetSubset)
