# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ossdbtoolsservice.utils.constants import MYSQL_PROVIDER_NAME
from tests.mocks.server_mock import ServerMock
from tests.utils import get_mock_logger


class ServiceProviderMock:

    def __init__(self, services: dict = {}):
        self._setup_mocks(get_mock_logger(), ServerMock(), services, MYSQL_PROVIDER_NAME)

    def registerMock(self, server, services: dict, logger=None):
        self._setup_mocks(logger, server, services)

    def _setup_mocks(self, logger, server, services, provider):
        self.logger = logger
        self.server = server
        self.provider = provider

        if services is not None:
            self._services = services

    def __getitem__(self, item: str):
        return self._services[item]
