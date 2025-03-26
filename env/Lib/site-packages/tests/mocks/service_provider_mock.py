# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from logging import Logger
from typing import TypeVar

from ossdbtoolsservice.hosting.service_provider import Service
from ossdbtoolsservice.utils import constants
from tests.mocks.server_mock import ServerMock
from tests.utils import get_mock_logger

S = TypeVar("S", bound="Service")


class ServiceProviderMock:
    def __init__(self, services: dict[str, Service] | None = None) -> None:
        self._setup_mocks(
            get_mock_logger(), ServerMock(), {} if services is None else services
        )

    def registerMock(
        self, server: ServerMock, services: dict, logger: Logger | None = None
    ) -> None:
        self._setup_mocks(logger, server, services)

    def _setup_mocks(
        self, logger: Logger | None, server: ServerMock, services: dict[str, Service]
    ) -> None:
        self.logger = logger
        self.server = server
        self.provider = constants.PG_PROVIDER_NAME

        if services is not None:
            self._services = services

    def __getitem__(self, item: str) -> Service:
        if not self._services:
            raise RuntimeError(
                "Service provider has not been initialized. Please call registerMock first."
            )
        s = self._services.get(item)
        if s is None:
            raise RuntimeError(
                f"Service {item} is not registered. Please register the service."
            )
        return s

    def get(self, item: str, class_: type[S]) -> S:
        """
        If the service exists, it is returned by its lookup key
        :param item: Key for looking up the service
        :raises RuntimeError: Service provider has not been initialized
        :return: The requested service
        """
        if item not in self._services:
            raise KeyError(f"Service '{item}' not found")

        service = self._services[item]
        if not isinstance(service, class_):
            raise TypeError(f"Service '{item}' is not of type {class_.__name__}")
        return service
