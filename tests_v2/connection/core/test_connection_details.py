from ossdbtoolsservice.connection.contracts.common import ConnectionDetails


def test_connection_details_hash_with_azure() -> None:
    """
    Test the hash function of ConnectionDetails with Azure.
    """
    details = ConnectionDetails.from_data( {
        "host": "localhost",
        "port": 5432,
        "dbname": "testdb",
        "user": "testuser",
        "azureAccountToken": "testtoken",
        "azureTokenExpiry": 1234567890,
    })

    # Represents the connection after a token refresh
    details_after_refresh = ConnectionDetails.from_data({
        "host": "localhost",
        "port": 5432,
        "dbname": "testdb",
        "user": "testuser",
        "azureAccountToken": "testtoken2",
        "azureTokenExpiry": 1234567891,
    })
    
    assert details.to_hash() == details_after_refresh.to_hash()