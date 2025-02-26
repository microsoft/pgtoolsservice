import argparse
from dataclasses import dataclass
from io import StringIO, TextIOBase
from pathlib import Path

import psycopg
import sqlparse
from psycopg.conninfo import make_conninfo

import tests_v2
from ossdbtoolsservice.utils.sql import as_sql
from tests_v2.test_utils.constants import DEFAULT_CONNECTION_STRING


@dataclass
class Dataset:
    name: str
    db_name: str
    scripts: list[str]

    def get_script_paths(self) -> list[Path]:
        return [
            Path(tests_v2.__file__).parent / "test_data" / self.name / script
            for script in self.scripts
        ]


DATASETS: list[Dataset] = [
    Dataset("pagila", db_name="pagila", scripts=["pagila-schema.sql", "pagila-data.sql"]),
]


def get_dataset(name: str) -> Dataset | None:
    for dataset in DATASETS:
        if dataset.name == name:
            return dataset
    return None


class DatasetLoader:
    def __init__(
        self, dataset: Dataset, admin_connection_string: str, db_name: str | None = None
    ) -> None:
        self.dataset = dataset
        self.admin_connection_string = admin_connection_string
        self.db_name = db_name or dataset.db_name

    def create_db(self) -> str:
        """Create the database and load the dataset.

        Returns:
            The connection string to the new database.
        """
        with psycopg.connect(self.admin_connection_string) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(as_sql(f"CREATE DATABASE {self.db_name}"))

        # Use psycopg.conninfo to robustly replace the dbname in the connection string.

        target_db_connection_string = make_conninfo(
            self.admin_connection_string, dbname=self.db_name
        )

        with psycopg.connect(target_db_connection_string) as conn:
            for script in self.dataset.get_script_paths():
                with conn.cursor() as cursor, conn.transaction(), open(script) as f:
                    execute_sql_dump(f, conn)
                    print(f"Executed {script}")

        return target_db_connection_string

    def drop_db(self) -> None:
        with psycopg.connect(self.admin_connection_string) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(as_sql(f"DROP DATABASE IF EXISTS {self.db_name}"))


def execute_sql_dump(file_obj: TextIOBase, conn: psycopg.Connection) -> None:
    """
    Executes all SQL statements from an open PostgreSQL dump file using a non-async
    psycopg3 connection, handling COPY commands with the copy() method.

    Args:
        file_obj: Open file object containing the SQL dump.
        conn: A psycopg3 connection.
    """
    # Buffer to accumulate non-COPY statements.
    statement_buffer: list[str] = []

    with conn.cursor() as cur:
        for line in file_obj:
            # Check if the line starts a COPY command (ignoring leading whitespace).
            if line.lstrip().upper().startswith("COPY "):
                # First, flush any buffered non-COPY statements.
                if statement_buffer:
                    statement_text = "".join(statement_buffer)
                    for stmt in sqlparse.split(statement_text):
                        if stmt.strip():
                            cur.execute(as_sql(stmt))
                    statement_buffer = []

                # Build the complete COPY command.
                copy_cmd = line
                # In some dumps the COPY command spans multiple lines,
                # so ensure it ends with a semicolon.
                while not copy_cmd.rstrip().endswith(";"):
                    try:
                        next_line = next(file_obj)
                    except StopIteration:
                        break
                    copy_cmd += next_line

                # Remove the trailing semicolon if present.
                # psycopg3 expects the command without it.
                if copy_cmd.strip().endswith(";"):
                    copy_cmd = copy_cmd.strip()[:-1]

                # Now, read the data lines for the COPY command
                # until the terminator "\." is found.
                copy_data_lines = []
                for data_line in file_obj:
                    if data_line.strip() == r"\.":
                        break
                    copy_data_lines.append(data_line)
                copy_data = StringIO("".join(copy_data_lines))

                # Execute the COPY command using the copy() method.
                with cur.copy(as_sql(copy_cmd)) as copy:
                    for data in copy_data:
                        copy.write(data)

            else:
                # Accumulate non-COPY lines.
                statement_buffer.append(line)

        # Finally, execute any remaining SQL statements.
        if statement_buffer:
            statement_text = "".join(statement_buffer)
            for stmt in sqlparse.split(statement_text):
                if stmt.strip():
                    cur.execute(as_sql(stmt))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", choices=[d.name for d in DATASETS])
    parser.add_argument("--connection-string", default=DEFAULT_CONNECTION_STRING)
    parser.add_argument("--drop", action="store_true")
    args = parser.parse_args()

    dataset = get_dataset(args.dataset)
    if dataset is None:
        raise ValueError(f"Dataset {args.dataset} not found")

    loader = DatasetLoader(dataset=dataset, admin_connection_string=args.connection_string)

    if args.drop:
        loader.drop_db()
    else:
        loader.create_db()
