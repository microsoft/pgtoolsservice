from ossdbtoolsservice.connection.contracts.common import ConnectionDetails
from ossdbtoolsservice.utils import constants


def get_connection_details_with_defaults(params: ConnectionDetails) -> ConnectionDetails:
    """Create new connection details with default values for missing params"""

    new_params = ConnectionDetails.from_data(params.options.copy())
    # Use the provider's default db if db name was not specified
    if params.database_name is None or params.database_name == "":
        is_cosmos = params.server_name and params.server_name.endswith(
            ".postgres.cosmos.azure.com"
        )

        db_key = constants.COSMOS_PG_DEFAULT_DB if is_cosmos else constants.PG_DEFAULT_DB
        new_params.database_name = constants.DEFAULT_DB[db_key]

    # Use the provider's default port if port number was not specified
    if not params.port:
        new_params.port = constants.DEFAULT_PORT[constants.PG_PROVIDER_NAME]

    # Use AzureAccountToken directly as a password
    if new_params.azure_account_token:
        new_params.password = new_params.azure_account_token

    return new_params


def is_same_connection_details(
    params1: ConnectionDetails, params2: ConnectionDetails
) -> bool:
    """Compare two connection details for equality, accounting for defaults"""

    # compare each detail, but include the default values on both sides
    params1 = get_connection_details_with_defaults(params1)
    params2 = get_connection_details_with_defaults(params2)
    return params1.options == params2.options
