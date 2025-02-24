"""Playback database that runs in a docker container.

For playback, the docker container needs to be freshly created
in order for playback database OIDs to match the recording session.
"""

import contextlib
import time
import uuid
from typing import Any

import docker
import psycopg
from psycopg.conninfo import make_conninfo

from tests_v2.test_utils.datasets import DatasetLoader, get_dataset


class PlaybackDB:
    def __init__(self, dataset_name: str) -> None:
        self._image = "mcr.microsoft.com/azurelinux/base/postgres:16"
        self._password = "example"
        self._port = 5678
        dataset = get_dataset(dataset_name)
        if dataset is None:
            raise ValueError(f"Dataset {dataset_name} not found")
        self.dataset = dataset
        # self.database_name = f"{dataset.db_name}-{uuid.uuid4().hex[:8]}"
        self.database_name = self.dataset.db_name

        self.db_config = {
            "host": "localhost",
            "port": self._port,
            "user": "postgres",
            "password": self._password,
            "dbname": "postgres",
        }
        self.admin_connection_string = make_conninfo(**self.db_config)
        self.loader: DatasetLoader | None = None
        self._target_db_connection_string: str | None = None

    @property
    def connection_string(self) -> str:
        if self._target_db_connection_string is None:
            raise ValueError("Database has not been created yet")
        return self._target_db_connection_string

    def __enter__(self) -> "PlaybackDB":
        """Create the database and load the dataset.

        Returns:
            The connection string to the new database.
        """
        client = docker.from_env()

        self._container = client.containers.run(
            self._image,
            name=f"pgts-playback-{self.database_name}-{uuid.uuid4().hex[:4]}",
            environment={
                "POSTGRES_PASSWORD": self._password,
            },
            ports={"5432/tcp": self._port},
            detach=True,
        )
        try:
            timeout = 10

            # Wait for the container to start
            start = time.time()
            while self._container.status != "running":
                self._container.reload()
                elapsed = time.time() - start
                if elapsed > timeout:
                    raise TimeoutError("Postgres container did not start in time")

            # Wait for the database to be ready
            start = time.time()
            while not self.is_postgres_available():
                elapsed = time.time() - start
                if elapsed > timeout:
                    raise TimeoutError("Postgres database did not start in time")

            self.loader = DatasetLoader(
                self.dataset, self.admin_connection_string, self.database_name
            )
            try:
                self._target_db_connection_string = self.loader.create_db()
                return self
            except Exception as e:
                self.loader.drop_db()
                raise RuntimeError("Failed to create database") from e
        except Exception as e:
            if self._container:
                with contextlib.suppress(Exception):
                    self._container.stop()
                    self._container.remove()
            raise RuntimeError("Failed to start database") from e

    def __exit__(self, *_: Any) -> None:
        self._target_db_connection_string = None
        # No reason to drop database, conatiner will be removed
        self._container.stop()
        self._container.remove()

    def is_postgres_available(self) -> bool:
        try:
            with psycopg.connect(**self.db_config) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                return True
        except psycopg.OperationalError:
            return False
