## Registered RPC methods 

### echo
- None
--- 

### version
- None
--- 

### shutdown
- None
--- 

### exit
- None
--- 

### admin/getdatabaseinfo
#### GetDatabaseInfoParameters
- options: `dict`
- owner_uri: `str`
--- 

### capabilities/list
#### CapabilitiesRequestParams
- host_name: `any`
- host_version: `any`
--- 

### initialize
#### InitializeRequestParams
- capabilities: `any`
- initialization_options: `any`
- process_id: `int`
- trace: `str`
- root_path: `str`
- root_uri: `str`
- workspace_folders: `str`
--- 

### connection/connect
#### ConnectRequestParams
- connection: `ConnectionDetails`
- owner_uri: `str`
- type: `ConnectionType`
--- 

### connection/disconnect
#### DisconnectRequestParams
- owner_uri: `any`
- type: `any`
--- 

### connection/listdatabases
#### ListDatabasesParams
- owner_uri: `str`
- include_details: `bool`
--- 

### connection/cancelconnect
#### CancelConnectParams
- owner_uri: `str`
- type: `ConnectionType`
--- 

### connection/changedatabase
#### ChangeDatabaseRequestParams
- owner_uri: `str`
- new_database: `str`
--- 

### connection/buildconnectioninfo
#### BuildConnectionInfoParams
- owner_uri: `str`
- type: `ConnectionType`
--- 

### connection/getconnectionstring
#### GetConnectionStringParams
- owner_uri: `str`
--- 

### backup/backup
#### BackupParams
- owner_uri: `str`
- backup_info: `BackupInfo`
- task_execution_mode: `any`
--- 

### restore/restore
#### RestoreParams
- owner_uri: `str`
- options: `RestoreOptions`
- task_execution_mode: `any`
--- 

### textDocument/completion
#### TextDocumentPosition
- text_document: `TextDocumentIdentifier`
- position: `Position`
--- 

### textDocument/definition
#### TextDocumentPosition
- text_document: `TextDocumentIdentifier`
- position: `Position`
--- 

### completionItem/resolve
#### CompletionItem
- label: `str`
- kind: `CompletionItemKind`
- detail: `str`
- documentation: `str`
- sort_text: `str`
- filter_text: `str`
- insert_text_format: `str`
- text_edit: `TextEdit`
- data: `any`
--- 

### textDocument/formatting
#### DocumentFormattingParams
- text_document: `TextDocumentIdentifier`
- options: `FormattingOptions`
--- 

### textDocument/rangeFormatting
#### DocumentRangeFormattingParams
- range: `Range`
- text_document: `TextDocumentIdentifier`
- options: `FormattingOptions`
--- 

### metadata/list
#### MetadataListParameters
- owner_uri: `str`
--- 

### objectexplorer/createsession
#### ConnectionDetails
- database_name: `any`
- port: `any`
- server_name: `any`
- user_name: `any`
- options: `dict`
--- 

### objectexplorer/closesession
#### CloseSessionParameters
- session_id: `str`
- owner_uri: `str`
- type: `int`
- options: `dict`
- server_name: `str`
- database_name: `str`
- user_name: `str`
--- 

### objectexplorer/expand
#### ExpandParameters
- session_id: `str`
- node_path: `str`
--- 

### objectexplorer/refresh
#### ExpandParameters
- session_id: `str`
- node_path: `str`
--- 

### query/executeString
#### ExecuteStringParams
- query: `str`
- owner_uri: `str`
- execution_plan_options: `ExecutionPlanOptions`
--- 

### query/executeDeploy
#### ExecuteStringParams
- query: `str`
- owner_uri: `str`
- execution_plan_options: `ExecutionPlanOptions`
--- 

### query/executeDocumentSelection
#### ExecuteDocumentSelectionParams
- query_selection: `SelectionData`
- owner_uri: `str`
- execution_plan_options: `ExecutionPlanOptions`
--- 

### query/executedocumentstatement
#### ExecuteDocumentStatementParams
- line: `int`
- column: `int`
- owner_uri: `str`
- execution_plan_options: `ExecutionPlanOptions`
--- 

### query/subset
#### SubsetParams
- owner_uri: `any`
- batch_index: `int`
- result_set_index: `int`
- rows_start_index: `int`
- rows_count: `int`
--- 

### query/cancel
#### QueryCancelParams
- owner_uri: `any`
--- 

### query/simpleexecute
#### SimpleExecuteRequest
- owner_uri: `str`
- query_string: `str`
--- 

### query/dispose
#### QueryDisposeParams
- owner_uri: `any`
--- 

### query/executionPlan
#### QueryExecutionPlanRequest
- owner_uri: `str`
- batch_index: `int`
- result_set_index: `int`
--- 

### query/saveCsv
#### SaveResultsAsCsvRequestParams
- is_save_selection: `any`
- include_headers: `bool`
- delimiter: `str`
- file_path: `str`
- batch_index: `int`
- result_set_index: `int`
- owner_uri: `str`
- row_start_index: `int`
- row_end_index: `int`
- column_start_index: `int`
- column_end_index: `int`
--- 

### query/saveJson
#### SaveResultsAsJsonRequestParams
- is_save_selection: `any`
- file_path: `str`
- batch_index: `int`
- result_set_index: `int`
- owner_uri: `str`
- row_start_index: `int`
- row_end_index: `int`
- column_start_index: `int`
- column_end_index: `int`
--- 

### query/saveExcel
#### SaveResultsAsExcelRequestParams
- is_save_selection: `any`
- include_headers: `bool`
- file_path: `str`
- batch_index: `int`
- result_set_index: `int`
- owner_uri: `str`
- row_start_index: `int`
- row_end_index: `int`
- column_start_index: `int`
- column_end_index: `int`
--- 

### scripting/script
#### ScriptAsParameters
- owner_uri: `str`
- operation: `ScriptOperation`
- scripting_objects: `List[ObjectMetadata]`
--- 

### edit/initialize
#### InitializeEditParams
- owner_uri: `str`
- schema_name: `str`
- object_type: `str`
- object_name: `str`
- query_string: `str`
- filters: `EditInitializerFilter`
--- 

### edit/subset
#### EditSubsetParams
- owner_uri: `str`
- row_start_index: `int`
- row_count: `int`
--- 

### edit/updateCell
#### UpdateCellRequest
- column_id: `any`
- new_value: `any`
- row_id: `any`
- owner_uri: `any`
--- 

### edit/createRow
#### CreateRowRequest
- owner_uri: `any`
--- 

### edit/deleteRow
#### DeleteRowRequest
- row_id: `any`
- owner_uri: `any`
--- 

### edit/revertCell
#### RevertCellRequest
- column_id: `int`
- row_id: `any`
- owner_uri: `any`
--- 

### edit/revertRow
#### RevertRowRequest
- row_id: `any`
- owner_uri: `any`
--- 

### edit/commit
#### EditCommitRequest
- owner_uri: `any`
--- 

### edit/dispose
#### DisposeRequest
- owner_uri: `any`
--- 

### tasks/canceltask
#### CancelTaskParameters
- task_id: `str`
--- 

### tasks/listtasks
#### ListTasksParameters
- list_active_tasks_only: `bool`
--- 

