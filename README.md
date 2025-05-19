# PostgreSQL Tools Service 

> NOTICE: This project is in the process of being archived. The code is still available for reference, but no further development or support will be provided.

New releases of this project can now be found at [pgsql-tools](https://github.com/microsoft/pgsql-tools).

##

The PostgreSQL Tools Service (pgtoolsservice, or PGTS) is an application that provides core functionality for various PostgreSQL Server tools.
* Connection management
* Language Service support using VS Code protocol
* Query execution and resultset management

It is based on an early version of [Microsoft SQL Tools Service](https://github.com/Microsoft/sqltoolsservice), with some functionality coming from [pgAdmin](https://www.pgadmin.org) and [pgcli](https://www.pgcli.com).

## Servers

There are two servers in PGTS: A RPC server that reads and writes JSON-RPC messages from stdin/stdout, and a web server that reads and writes JSON-RPC messages over HTTP using web sockets.
The web server is used to provide a REST API for the RPC server.
Both servers use messaging defined by the [Language Server Protocol (LSP)](https://microsoft.github.io/language-server-protocol/).

## Naming

The project is named `pgtoolsservice`, but there is the name `ossdbtoolsservice` in some places. This reflects a refactor that was done years ago to make the project more generic and support other databases.
However, that refactor was never completed, and the project is still PostgreSQL specific. The name `ossdbtoolsservice` will be removed in a future release.

## Support
Support for this extension is provided on our [GitHub Issue Tracker]. You can submit a [bug report], a [feature suggestion] or participate in discussions.

## Contributing to the Extension
See the [developer documentation] for details on how to contribute to this extension.

## Code of Conduct
This project has adopted the [Microsoft Open Source Code of Conduct]. For more information see the [Code of Conduct FAQ] or contact [opencode@microsoft.com] with any additional questions or comments.

## Privacy Statement
The [Microsoft Enterprise and Developer Privacy Statement] describes the privacy statement of this software.

## License
This extension is [licensed under the MIT License]. Please see the [third-party notices] file for additional copyright notices and license terms applicable to portions of the software.

## Developing

See the [DEVELOPING.md](DEVELOPING.md) for details on how to develop this project.


[GitHub Issue Tracker]:https://github.com/Microsoft/pgtoolsservice/issues
[bug report]:https://github.com/Microsoft/pgtoolsservice/issues/new?labels=bug
[feature suggestion]:https://github.com/Microsoft/pgtoolsservice/issues/new?labels=feature-request
[developer documentation]:https://github.com/Microsoft/pgtoolsservice/wiki/How-to-Contribute
[Microsoft Enterprise and Developer Privacy Statement]:https://go.microsoft.com/fwlink/?LinkId=786907&lang=en7
[licensed under the MIT License]:https://github.com/Microsoft/pgtoolsservice/blob/main/License.txt
[third-party notices]: https://github.com/Microsoft/pgtoolsservice/blob/main/ThirdPartyNotices.txt
[Microsoft Open Source Code of Conduct]:https://opensource.microsoft.com/codeofconduct/
[Code of Conduct FAQ]:https://opensource.microsoft.com/codeofconduct/faq/
[opencode@microsoft.com]:mailto:opencode@microsoft.com
