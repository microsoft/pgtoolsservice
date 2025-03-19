# Dictionary mapping connection option names to their
# corresponding PostgreSQL connection string keys.
# If a name is not present in this map, the name should be used as the key.
PG_CONNECTION_OPTION_KEY_MAP = {
    "connectTimeout": "connect_timeout",
    "clientEncoding": "client_encoding",
    "applicationName": "application_name",
}

# Recognized parameter keywords for postgres database connection
# Source: https://www.postgresql.org/docs/9.6/static/libpq-connect.html#LIBPQ-PARAMKEYWORDS
PG_CONNECTION_PARAM_KEYWORDS = [
    "host",
    "hostaddr",
    "port",
    "dbname",
    "user",
    "password",
    "passfile",
    "connect_timeout",
    "client_encoding",
    "options",
    "application_name",
    "fallback_application_name",
    "keepalives",
    "keepalives_idle",
    "keepalives_interval",
    "keepalives_count",
    "tty",
    "sslmode",
    "requiressl",
    "sslcompression",
    "sslcert",
    "sslkey",
    "sslrootcert",
    "sslcrl",
    "requirepeer",
    "krbsrvname",
    "gsslib",
    "service",
    "target_session_attrs",
]
