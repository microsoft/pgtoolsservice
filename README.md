# Open Source Databases Tools Service 
The Open Source Databases Tools Service is an application that provides core functionality for various PostgreSQL Server tools.  These features include the following:
* Connection management
* Language Service support using VS Code protocol
* Query execution and resultset management

It is based on the [Microsoft SQL Tools Service](https://github.com/Microsoft/sqltoolsservice) and [pgAdmin](https://www.pgadmin.org).

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

## Development Installation

To install the package in development mode, run:

    pip install -e .[dev]

This installs an editable version of the package with extra development dependencies.
This is required for running the VS Code extension in development.

## Running tests

There are two test projects in the repository, `tests` and `tests_v2`.
The `tests_v2` are newer tests that are run with pytest.
To run the `tests` tests, run: `scripts/test_all.sh` or `scripts/test_all.ps1` if you are on Windows.
To run the `tests_v2` tests, run: `pytest tests_v2`.

### Docker postgres

To run the integration tests, which are marked across the `tests` with a `@integration` decorator, you need to have a running postgres instance.
You can use the `docker-compose` file to quickly spin up a local postgres instance.

```bash
docker-compose up -d
```
This will create a local postgres instance with the following connection string:

```
postgresql://postgres:example@localhost:5432/postgres
```


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
