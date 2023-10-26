# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# This module holds the error resource constants for ossdb tools service errors

# INTERNAL ERROR CODES. According to the standard, the first two characters of an error code denote a class of errors, while the last three characters indicate a specific condition within that class
# Read more here: https://www.postgresql.org/docs/current/errcodes-appendix.html
REQUEST_METHOD_PROCESSING_UNHANDLED_EXCEPTION = 'AD004'
EXECUTE_QUERY_GET_CONNECTION_ERROR = 'AD005'
EXECUTE_DEPLOY_GET_CONNECTION_ERROR = 'AD006'
CANCEL_QUERY_ERROR = 'AD007'
DISPOSE_QUERY_REQUEST_ERROR = 'AD008'
UNSUPPORTED_REQUEST_METHOD = 'AD009'
LIST_DATABASE_GET_CONNECTION_VALUE_ERROR = 'AD010'
LIST_DATABASE_ERROR = 'AD011'
EDIT_DATA_CUSTOM_QUERY_UNSUPPORTED_ERROR = 'AD012'
EDIT_DATA_COMMIT_FAILURE = 'AD013'
EDIT_DATA_SESSION_NOT_FOUND = 'AD014'
EDIT_DATA_SESSION_OPERATION_FAILURE = 'AD015'
GET_METADATA_FAILURE = 'AD016'
OBJECT_EXPLORER_CREATE_SESSION_ERROR = 'AD017'
OBJECT_EXPLORER_CLOSE_SESSION_ERROR = 'AD018'
OBJECT_EXPLORER_EXPAND_NODE_ERROR = 'AD019'
ANOTHER_QUERY_EXECUTING_ERROR = 'AD020'
DISPOSE_REQUEST_NO_QUERY_ERROR = 'AD021'
SAVE_QUERY_RESULT_ERROR = 'AD022'
SCRIPTAS_REQUEST_ERROR = 'AD023'
UNKNOWN_CONNECTION_ERROR = 'AD024'
PSYCOPG_DRIVER_UNKNOWN_ERROR_CODE = 'AD025'
NEW_DATABASE_GET_CHARSETS_ERROR_CODE = 'AD026'
NEW_DATABASE_GET_COLLATIONS_ERROR_CODE = 'AD027'
NEW_DATABASE_CREATE_ERROR_CODE = 'AD028'
BUILD_CONNECTION_ERROR_CODE = 'AD029'
LIST_METADATA_FAILURE_ERROR_CODE = 'AD030'

# ErrorTelemetryViews
CONNECTION = 'Connection'
EDIT_DATA = 'Edit Data'
JSON_RPC = 'Json Rpc'
METADATA = 'Metadata'
OBJECT_EXPLORER = 'Object Explorer'
QUERY_EXECUTION = 'Query Execution'
SCRIPTING = 'Scripting'

# ErrorTelmetryNames
LIST_DATABASES_CONNECTION_VALUE_ERROR = 'List Databases Connection Value Error'
LIST_DATABASES_ERROR = 'List Databases Error'
BUILD_CONNECTION_ERROR = 'Build Connection Error'
EDIT_DATA_CUSTOM_QUERY = 'Edit Data Custom Query Unsupported'
EDIT_DATA_COMMIT = 'Edit Data Commit Failure'
EDIT_DATA_SESSION_NOT_FOUND = 'Edit Data Session Not Found'
EDIT_DATA_SESSION_OPERATION = 'Edit Data Session Operation Failure'
UNSUPPORTED_REQUEST = 'Unsupported Request Method'
REQUEST_METHOD_PROCESSING = 'Request Method Processing Unhandled Exception'
LIST_METADATA_FAILURE = 'List Metadata Failure'
OBJECT_EXPLORER_CREATE_SESSION = 'Object Explorer Create Session Error'
OBJECT_EXPLORER_CLOSE_SESSION = 'Object Explorer Close Session Error'
OBJECT_EXPLORER_EXPAND_NODE = 'Object Explorer Expand Node Error'
EXECUTE_QUERY_GET_CONNECTION = 'Execute Query Get Connection Error'
EXECUTE_DEPLOY_GET_CONNECTION = 'Execute Deploy Get Connection Error'
ANOTHER_QUERY_EXECUTING = 'Another Query Executing Error'
CANCEL_QUERY = 'Cancel Query'
DISPOSE_QUERY_NO_QUERY = 'Dispose Query No Query Error'
DISPOSE_QUERY_REQUEST = 'Dispose Query Request Error'
SAVE_QUERY_RESULT = 'Save Query Result Error'
SCRIPT_AS_REQUEST = 'Script As Request Error'
