import unittest
from unittest import mock

from ossdbtoolsservice.connection import ConnectionService
from ossdbtoolsservice.driver.types.psycopg_driver import PostgreSQLConnection
from ossdbtoolsservice.hosting import ServiceProvider
from ossdbtoolsservice.query_execution.contracts import ExecuteStringParams, SubsetParams
from ossdbtoolsservice.query_execution.query_execution_service import QueryExecutionService
from ossdbtoolsservice.utils import constants
from tests.integration import get_connection_details, integration_test
import tests.utils as utils


class TestConverters(unittest.TestCase):

    def setUp(self):
        self.query_execution_service = QueryExecutionService()
        self.connection_service = ConnectionService()
        self.service_provider = ServiceProvider(None, {}, constants.PG_PROVIDER_NAME)
        self.service_provider._services = {constants.CONNECTION_SERVICE_NAME: self.connection_service}
        self.service_provider._is_initialized = True
        self.query_execution_service._service_provider = self.service_provider
        self.request_context = utils.MockRequestContext()

    # if bool type has bool and bool_array while varchar[] is array type
    def generic_test(self, connection, value, pg_cast, array_type_only=False):
        request_params = ExecuteStringParams()
        request_params.owner_uri = 'test_uri'

        array_query = f"SELECT ARRAY[NULL::{pg_cast}]; SELECT ARRAY[{value}, {value}]::{pg_cast}[];"
        scalar_query = f"SELECT NULL::{pg_cast}; SELECT {value}::{pg_cast};" if not array_type_only else ""

        request_params.query = array_query + scalar_query
        num_times = 2 if array_type_only else 4

        mock_thread = utils.MockThread()
        with mock.patch('threading.Thread', new=mock.Mock(side_effect=mock_thread.initialize_target)):
            self.query_execution_service._handle_execute_query_request(self.request_context, request_params)

        cursor = connection.cursor()
        cursor.execute(request_params.query)
        expected_results = []
        while cursor:
            expected_result = cursor.fetchall()
            expected_results.append(expected_result)
            if not cursor.nextset():
                break

        for i in range(num_times):
            self._execute_query(request_params, i)
            self._compare_results(expected_results, i)

    def _execute_query(self, request_params, batch_index):
        subset_params = SubsetParams().from_dict({
            'ownerUri': request_params.owner_uri,
            'resultSetIndex': 0,
            'rowsCount': 1,
            'rowsStartIndex': 0,
            'batchIndex': batch_index
        })
        self.query_execution_service._handle_subset_request(self.request_context, subset_params)

    def _compare_results(self, expected_results, batch_index):
        query_results = self.request_context.last_response_params.result_subset

        actual_value = query_results.rows[0][0].raw_object
        expected_value = expected_results[batch_index][0][0]

        expected_value = str(expected_value).replace('None', 'null').replace('\"', '\'')
        actual_value = str(actual_value).replace('None', 'null').replace('\"', '\'')

        self.assertEqual(actual_value, expected_value)

    @integration_test
    def test_datatypes_converters(self):
        connection = PostgreSQLConnection(get_connection_details())
        self.connection_service.get_connection = mock.Mock(return_value=connection)
        self.generic_test(connection, 'true', 'bool')
        self.generic_test(connection, '5.67', 'real')
        self.generic_test(connection, '8.912', 'double precision')
        self.generic_test(connection, '123', 'smallint')
        self.generic_test(connection, '123456', 'integer')
        self.generic_test(connection, '1234567890', 'bigint')
        self.generic_test(connection, '1234.5678', 'numeric')
        self.generic_test(connection, "'hello'", 'bpchar')
        self.generic_test(connection, "'2023-01-01'", 'date')
        self.generic_test(connection, "'12:34:56'", 'time')
        self.generic_test(connection, "'12:34:56+00'", 'timetz')
        self.generic_test(connection, "'2023-01-01 12:34:56'", 'timestamp')
        self.generic_test(connection, "'2023-01-01 12:34:56+00'", 'timestamptz')
        self.generic_test(connection, "'1 year 2 months 5 days 3 hours'", 'interval')
        self.generic_test(connection, "'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'", 'uuid')
        self.generic_test(connection, r"E'\\xDEADBEEF'", 'bytea')
        self.generic_test(connection, "'{\"key\": \"value\"}'", 'json')
        self.generic_test(connection, "'{\"key\": \"value\"}'", 'jsonb')
        self.generic_test(connection, "'[1,10]'", 'int4range')
        self.generic_test(connection, "'[1,1000000000]'", 'int8range')
        self.generic_test(connection, "'[2.2,10.3]'", 'numrange')
        self.generic_test(connection, "'[2023-01-01 12:34, 2023-01-01 12:35]'", 'tsrange')
        self.generic_test(connection, "'[2023-01-01 12:34+00, 2023-01-01 12:35+00]'", 'tstzrange')
        self.generic_test(connection, "'[2023-01-01, 2023-01-02]'", 'daterange')
        self.generic_test(connection, '123456', 'oid')

        # INET
        self.generic_test(connection, "'192.168.1.1'", 'inet')
        self.generic_test(connection, "'192.168.1.1/24'", 'inet')
        self.generic_test(connection, "'2001:0db8:85a3:0000:0000:8a2e:0370:7334'", 'inet')
        self.generic_test(connection, "'2001:0db8:85a3:0000:0000:8a2e:0370:7334/64'", 'inet')

        # CIDR
        self.generic_test(connection, "'192.168.1.0/24'", 'cidr')
        self.generic_test(connection, "'2001:0db8:85a3::/64'", 'cidr')

        # MAC address type and its array
        self.generic_test(connection, "'08:00:2b:01:02:03'", 'macaddr')

        # Bit and its array
        self.generic_test(connection, "B'1101'", 'bit')
        self.generic_test(connection, "B'11010'", 'bit varying')

        # tsvector and its array
        self.generic_test(connection, "'hello world'", 'tsvector')
        self.generic_test(connection, "'hello & world'", 'tsquery')

        # xml and its array
        self.generic_test(connection, "'<tag>Hello world</tag>'", 'xml')

        # Geometric types
        geometric_values = {
            'point': "'(1,2)'",
            'line': "'{1,2,3}'",
            'lseg': "'[(1,2),(3,4)]'",
            'box': "'((1,2),(3,4))'",
            'path': "'[(1,2),(3,4),(5,6)]'",
            'polygon': "'((1,2),(3,4),(5,6))'",
            'circle': "'<(1,2),3>'"
        }

        for geo_type, geo_value in geometric_values.items():
            self.generic_test(connection, geo_value, geo_type)

        # OID related types
        oid_types = [
            'regproc', 'regprocedure', 'regoper', 'regoperator',
            'regclass', 'regtype', 'regrole', 'regnamespace',
            'regconfig', 'regdictionary'
        ]

        for oid_type in oid_types:
            self.generic_test(connection, '1234', oid_type)

        self.generic_test(connection, "'0/0'", 'pg_lsn')

        # array only data types
        self.generic_test(connection, "ARRAY['abc', 'def']", 'varchar[]', True)
        self.generic_test(connection, "ARRAY['a'::char, 'b']", 'char[]', True)
        self.generic_test(connection, "ARRAY['abc', 'def']", 'text[]', True)
