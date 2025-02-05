# Index

## base
- [echo](#echo)
- [version](#version)
- [shutdown](#shutdown)
- [exit](#exit)
- [initialize](#initialize)

## admin
- [admin/getdatabaseinfo](#admingetdatabaseinfo)

## capabilities
- [capabilities/list](#capabilitieslist)

## connection
- [connection/connect](#connectionconnect)
- [connection/disconnect](#connectiondisconnect)
- [connection/listdatabases](#connectionlistdatabases)
- [connection/cancelconnect](#connectioncancelconnect)
- [connection/changedatabase](#connectionchangedatabase)
- [connection/buildconnectioninfo](#connectionbuildconnectioninfo)
- [connection/getconnectionstring](#connectiongetconnectionstring)

## backup
- [backup/backup](#backupbackup)

## restore
- [restore/restore](#restorerestore)

## textDocument
- [textDocument/completion](#textdocumentcompletion)
- [textDocument/definition](#textdocumentdefinition)
- [textDocument/formatting](#textdocumentformatting)
- [textDocument/rangeFormatting](#textdocumentrangeformatting)

## completionItem
- [completionItem/resolve](#completionitemresolve)

## metadata
- [metadata/list](#metadatalist)

## objectexplorer
- [objectexplorer/createsession](#objectexplorercreatesession)
- [objectexplorer/closesession](#objectexplorerclosesession)
- [objectexplorer/expand](#objectexplorerexpand)
- [objectexplorer/refresh](#objectexplorerrefresh)

## query
- [query/executeString](#queryexecutestring)
- [query/executeDeploy](#queryexecutedeploy)
- [query/executeDocumentSelection](#queryexecutedocumentselection)
- [query/executedocumentstatement](#queryexecutedocumentstatement)
- [query/subset](#querysubset)
- [query/cancel](#querycancel)
- [query/simpleexecute](#querysimpleexecute)
- [query/dispose](#querydispose)
- [query/executionPlan](#queryexecutionplan)
- [query/saveCsv](#querysavecsv)
- [query/saveJson](#querysavejson)
- [query/saveExcel](#querysaveexcel)

## scripting
- [scripting/script](#scriptingscript)

## edit
- [edit/initialize](#editinitialize)
- [edit/subset](#editsubset)
- [edit/updateCell](#editupdatecell)
- [edit/createRow](#editcreaterow)
- [edit/deleteRow](#editdeleterow)
- [edit/revertCell](#editrevertcell)
- [edit/revertRow](#editrevertrow)
- [edit/commit](#editcommit)
- [edit/dispose](#editdispose)

## tasks
- [tasks/canceltask](#taskscanceltask)
- [tasks/listtasks](#taskslisttasks)



# Requests

# base

## echo
- **Class**: None
- **Method**: echo
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "echo",
    "id": 833411,
    "params": null
}
```

## version
- **Class**: None
- **Method**: version
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "version",
    "id": 954123,
    "params": null
}
```

## shutdown
- **Class**: None
- **Method**: shutdown
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "shutdown",
    "id": 967675,
    "params": null
}
```

## exit
- **Class**: None
- **Method**: exit
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "exit",
    "id": 21451,
    "params": null
}
```

## initialize
- **Class**: InitializeRequestParams
- **Method**: initialize
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "initialize",
    "id": 396735,
    "params": {
        "capabilities": null,
        "initializationOptions": null,
        "processId": null,
        "trace": null,
        "rootPath": null,
        "rootUri": null,
        "workspaceFolders": null
    }
}
```

# admin

## admin/getdatabaseinfo
- **Class**: GetDatabaseInfoParameters
- **Method**: admin/getdatabaseinfo
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "admin/getdatabaseinfo",
    "id": 748689,
    "params": {
        "options": null,
        "ownerUri": null
    }
}
```

# capabilities

## capabilities/list
- **Class**: CapabilitiesRequestParams
- **Method**: capabilities/list
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "capabilities/list",
    "id": 715483,
    "params": {
        "hostName": null,
        "hostVersion": null
    }
}
```

# connection

## connection/connect
- **Class**: ConnectRequestParams
- **Method**: connection/connect
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "connection/connect",
    "id": 489387,
    "params": {
        "connection": {
            "options": {}
        },
        "ownerUri": null,
        "type": "Default"
    }
}
```

## connection/disconnect
- **Class**: DisconnectRequestParams
- **Method**: connection/disconnect
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "connection/disconnect",
    "id": 333819,
    "params": {
        "ownerUri": null,
        "type": null
    }
}
```

## connection/listdatabases
- **Class**: ListDatabasesParams
- **Method**: connection/listdatabases
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "connection/listdatabases",
    "id": 477800,
    "params": {
        "ownerUri": null,
        "includeDetails": null
    }
}
```

## connection/cancelconnect
- **Class**: CancelConnectParams
- **Method**: connection/cancelconnect
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "connection/cancelconnect",
    "id": 81133,
    "params": {
        "ownerUri": "CJKqObRb",
        "type": "Default"
    }
}
```

## connection/changedatabase
- **Class**: ChangeDatabaseRequestParams
- **Method**: connection/changedatabase
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "connection/changedatabase",
    "id": 82544,
    "params": {
        "ownerUri": null,
        "newDatabase": null,
        "connection": {
            "options": {}
        }
    }
}
```

## connection/buildconnectioninfo
- **Class**: BuildConnectionInfoParams
- **Method**: connection/buildconnectioninfo
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "connection/buildconnectioninfo",
    "id": 331139,
    "params": {
        "ownerUri": "bbjiWQhZ",
        "type": "Default"
    }
}
```

## connection/getconnectionstring
- **Class**: GetConnectionStringParams
- **Method**: connection/getconnectionstring
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "connection/getconnectionstring",
    "id": 170702,
    "params": {
        "ownerUri": "PUydPakY"
    }
}
```

# backup

## backup/backup
- **Class**: BackupParams
- **Method**: backup/backup
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "backup/backup",
    "id": 846133,
    "params": {
        "ownerUri": null,
        "backupInfo": {
            "type": "dump",
            "path": null,
            "jobs": null,
            "compress": null,
            "dataOnly": null,
            "blobs": null,
            "clean": null,
            "create": null,
            "encoding": null,
            "schema": null,
            "excludeSchema": null,
            "oids": null,
            "noOwner": null,
            "schemaOnly": null,
            "superuser": null,
            "table": null,
            "excludeTable": null,
            "noPrivileges": null,
            "columnInserts": null,
            "disableDollarQuoting": null,
            "disableTriggers": null,
            "enableRowSecurity": null,
            "excludeTableData": null,
            "ifExists": null,
            "inserts": null,
            "noSecurityLabels": null,
            "noSynchronizedSnapshots": null,
            "noTablespaces": null,
            "noUnloggedTableData": null,
            "quoteAllIdentifiers": null,
            "section": null,
            "serializableDeferrable": null,
            "snapshot": null,
            "strictNames": null,
            "useSetSessionAuthorization": null
        },
        "taskExecutionMode": null
    }
}
```

# restore

## restore/restore
- **Class**: RestoreParams
- **Method**: restore/restore
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "restore/restore",
    "id": 404511,
    "params": {
        "ownerUri": null,
        "options": {
            "path": null,
            "dataOnly": null,
            "clean": null,
            "create": null,
            "exitOnError": null,
            "index": null,
            "jobs": null,
            "useList": null,
            "schema": null,
            "noOwner": null,
            "function": null,
            "schemaOnly": null,
            "superuser": null,
            "table": null,
            "trigger": null,
            "noPrivileges": null,
            "singleTransaction": null,
            "disableTriggers": null,
            "enableRowSecurity": null,
            "ifExists": null,
            "noDataForFailedTables": null,
            "noSecurityLabels": null,
            "noTablespaces": null,
            "section": null,
            "strictNames": null,
            "role": null
        },
        "taskExecutionMode": null
    }
}
```

# textDocument

## textDocument/completion
- **Class**: TextDocumentPosition
- **Method**: textDocument/completion
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "textDocument/completion",
    "id": 535868,
    "params": {
        "textDocument": {
            "uri": null
        },
        "position": {
            "line": 0,
            "character": 0
        }
    }
}
```

## textDocument/definition
- **Class**: TextDocumentPosition
- **Method**: textDocument/definition
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "textDocument/definition",
    "id": 408334,
    "params": {
        "textDocument": {
            "uri": null
        },
        "position": {
            "line": 0,
            "character": 0
        }
    }
}
```

## textDocument/formatting
- **Class**: DocumentFormattingParams
- **Method**: textDocument/formatting
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "textDocument/formatting",
    "id": 156638,
    "params": {
        "textDocument": {
            "uri": null
        },
        "options": {
            "tabSize": null,
            "insertSpaces": null
        }
    }
}
```

## textDocument/rangeFormatting
- **Class**: DocumentRangeFormattingParams
- **Method**: textDocument/rangeFormatting
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "textDocument/rangeFormatting",
    "id": 802441,
    "params": {
        "textDocument": {
            "uri": null
        },
        "options": {
            "tabSize": null,
            "insertSpaces": null
        },
        "range": {
            "start": {
                "line": 0,
                "character": 0
            },
            "end": {
                "line": 0,
                "character": 0
            }
        }
    }
}
```

# completionItem

## completionItem/resolve
- **Class**: CompletionItem
- **Method**: completionItem/resolve
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "completionItem/resolve",
    "id": 850260,
    "params": {
        "label": null,
        "kind": 1,
        "detail": null,
        "documentation": null,
        "sortText": null,
        "filterText": null,
        "insertTextFormat": null,
        "textEdit": {
            "range": {
                "start": {
                    "line": 0,
                    "character": 0
                },
                "end": {
                    "line": 0,
                    "character": 0
                }
            },
            "newText": null
        },
        "data": null
    }
}
```

# metadata

## metadata/list
- **Class**: MetadataListParameters
- **Method**: metadata/list
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "metadata/list",
    "id": 363490,
    "params": {
        "ownerUri": null
    }
}
```

# objectexplorer

## objectexplorer/createsession
- **Class**: ConnectionDetails
- **Method**: objectexplorer/createsession
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "objectexplorer/createsession",
    "id": 277830,
    "params": {
        "options": {}
    }
}
```

## objectexplorer/closesession
- **Class**: CloseSessionParameters
- **Method**: objectexplorer/closesession
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "objectexplorer/closesession",
    "id": 410330,
    "params": {
        "sessionId": null,
        "ownerUri": null,
        "type": null,
        "options": null,
        "serverName": null,
        "databaseName": null,
        "userName": null
    }
}
```

## objectexplorer/expand
- **Class**: ExpandParameters
- **Method**: objectexplorer/expand
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "objectexplorer/expand",
    "id": 445930,
    "params": {
        "sessionId": null,
        "nodePath": null
    }
}
```

## objectexplorer/refresh
- **Class**: ExpandParameters
- **Method**: objectexplorer/refresh
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "objectexplorer/refresh",
    "id": 414031,
    "params": {
        "sessionId": null,
        "nodePath": null
    }
}
```

# query

## query/executeString
- **Class**: ExecuteStringParams
- **Method**: query/executeString
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "query/executeString",
    "id": 430231,
    "params": {
        "ownerUri": null,
        "executionPlanOptions": {
            "includeActualExecutionPlanXml": false,
            "includeEstimatedExecutionPlanXml": false
        },
        "query": null
    }
}
```

## query/executeDeploy
- **Class**: ExecuteStringParams
- **Method**: query/executeDeploy
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "query/executeDeploy",
    "id": 572825,
    "params": {
        "ownerUri": null,
        "executionPlanOptions": {
            "includeActualExecutionPlanXml": false,
            "includeEstimatedExecutionPlanXml": false
        },
        "query": null
    }
}
```

## query/executeDocumentSelection
- **Class**: ExecuteDocumentSelectionParams
- **Method**: query/executeDocumentSelection
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "query/executeDocumentSelection",
    "id": 74770,
    "params": {
        "ownerUri": null,
        "executionPlanOptions": {
            "includeActualExecutionPlanXml": false,
            "includeEstimatedExecutionPlanXml": false
        },
        "querySelection": {
            "startLine": 77,
            "startColumn": 29,
            "endLine": 70,
            "endColumn": 46
        }
    }
}
```

## query/executedocumentstatement
- **Class**: ExecuteDocumentStatementParams
- **Method**: query/executedocumentstatement
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "query/executedocumentstatement",
    "id": 541577,
    "params": {
        "ownerUri": null,
        "executionPlanOptions": {
            "includeActualExecutionPlanXml": false,
            "includeEstimatedExecutionPlanXml": false
        },
        "line": null,
        "column": null
    }
}
```

## query/subset
- **Class**: SubsetParams
- **Method**: query/subset
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "query/subset",
    "id": 191513,
    "params": {
        "ownerUri": null,
        "batchIndex": null,
        "resultSetIndex": null,
        "rowsStartIndex": null,
        "rowsCount": null
    }
}
```

## query/cancel
- **Class**: QueryCancelParams
- **Method**: query/cancel
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "query/cancel",
    "id": 939900,
    "params": {
        "ownerUri": null
    }
}
```

## query/simpleexecute
- **Class**: SimpleExecuteRequest
- **Method**: query/simpleexecute
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "query/simpleexecute",
    "id": 771827,
    "params": {
        "ownerUri": null,
        "queryString": null
    }
}
```

## query/dispose
- **Class**: QueryDisposeParams
- **Method**: query/dispose
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "query/dispose",
    "id": 702998,
    "params": {
        "ownerUri": null
    }
}
```

## query/executionPlan
- **Class**: QueryExecutionPlanRequest
- **Method**: query/executionPlan
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "query/executionPlan",
    "id": 204540,
    "params": {
        "ownerUri": null,
        "batchIndex": null,
        "resultSetIndex": null
    }
}
```

## query/saveCsv
- **Class**: SaveResultsAsCsvRequestParams
- **Method**: query/saveCsv
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "query/saveCsv",
    "id": 820266,
    "params": {
        "filePath": null,
        "batchIndex": null,
        "resultSetIndex": null,
        "ownerUri": null,
        "rowStartIndex": null,
        "rowEndIndex": null,
        "columnStartIndex": null,
        "columnEndIndex": null,
        "includeHeaders": null,
        "delimiter": ","
    }
}
```

## query/saveJson
- **Class**: SaveResultsAsJsonRequestParams
- **Method**: query/saveJson
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "query/saveJson",
    "id": 23040,
    "params": {
        "filePath": null,
        "batchIndex": null,
        "resultSetIndex": null,
        "ownerUri": null,
        "rowStartIndex": null,
        "rowEndIndex": null,
        "columnStartIndex": null,
        "columnEndIndex": null
    }
}
```

## query/saveExcel
- **Class**: SaveResultsAsExcelRequestParams
- **Method**: query/saveExcel
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "query/saveExcel",
    "id": 194377,
    "params": {
        "filePath": null,
        "batchIndex": null,
        "resultSetIndex": null,
        "ownerUri": null,
        "rowStartIndex": null,
        "rowEndIndex": null,
        "columnStartIndex": null,
        "columnEndIndex": null,
        "includeHeaders": null
    }
}
```

# scripting

## scripting/script
- **Class**: ScriptAsParameters
- **Method**: scripting/script
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "scripting/script",
    "id": 89810,
    "params": {
        "ownerUri": null,
        "operation": 0,
        "scriptingObjects": null,
        "metadata": {
            "metadataType": 0,
            "metadataTypeName": "rkzmgHYq",
            "name": "ApzGCxZe",
            "schema": null,
            "urn": "bHIZPhzc"
        }
    }
}
```

# edit

## edit/initialize
- **Class**: InitializeEditParams
- **Method**: edit/initialize
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "edit/initialize",
    "id": 177406,
    "params": {
        "ownerUri": null,
        "schemaName": null,
        "objectType": null,
        "objectName": null,
        "queryString": null,
        "filters": {
            "limitResults": null
        }
    }
}
```

## edit/subset
- **Class**: EditSubsetParams
- **Method**: edit/subset
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "edit/subset",
    "id": 905356,
    "params": {
        "ownerUri": null,
        "rowStartIndex": null,
        "rowCount": null
    }
}
```

## edit/updateCell
- **Class**: UpdateCellRequest
- **Method**: edit/updateCell
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "edit/updateCell",
    "id": 225257,
    "params": {
        "ownerUri": null,
        "rowId": null,
        "columnId": null,
        "newValue": null
    }
}
```

## edit/createRow
- **Class**: CreateRowRequest
- **Method**: edit/createRow
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "edit/createRow",
    "id": 3650,
    "params": {
        "ownerUri": null
    }
}
```

## edit/deleteRow
- **Class**: DeleteRowRequest
- **Method**: edit/deleteRow
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "edit/deleteRow",
    "id": 392809,
    "params": {
        "ownerUri": null,
        "rowId": null
    }
}
```

## edit/revertCell
- **Class**: RevertCellRequest
- **Method**: edit/revertCell
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "edit/revertCell",
    "id": 392587,
    "params": {
        "ownerUri": null,
        "rowId": null,
        "columnId": null
    }
}
```

## edit/revertRow
- **Class**: RevertRowRequest
- **Method**: edit/revertRow
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "edit/revertRow",
    "id": 220785,
    "params": {
        "ownerUri": null,
        "rowId": null
    }
}
```

## edit/commit
- **Class**: EditCommitRequest
- **Method**: edit/commit
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "edit/commit",
    "id": 991006,
    "params": {
        "ownerUri": null
    }
}
```

## edit/dispose
- **Class**: DisposeRequest
- **Method**: edit/dispose
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "edit/dispose",
    "id": 853550,
    "params": {
        "ownerUri": null
    }
}
```

# tasks

## tasks/canceltask
- **Class**: CancelTaskParameters
- **Method**: tasks/canceltask
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "tasks/canceltask",
    "id": 249908,
    "params": {
        "taskId": null
    }
}
```

## tasks/listtasks
- **Class**: ListTasksParameters
- **Method**: tasks/listtasks
- **Request JSON**:
```json
{
    "jsonrpc": "2.0",
    "method": "tasks/listtasks",
    "id": 306468,
    "params": {
        "listActiveTasksOnly": null
    }
}
```

