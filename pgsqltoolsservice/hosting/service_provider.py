# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from logging import Logger
from typing import Optional

from pgsqltoolsservice.hosting import JSONRPCServer


class ServiceProvider:
    def __init__(self, json_rpc_server: JSONRPCServer, services: dict, provider: str, logger: Optional[Logger] = None):
        self._is_initialized = False
        self._logger = logger
        self._server = json_rpc_server
        self._provider_name = provider
        self._services = {service_name: service_class() for (service_name, service_class) in services.items()}
        

    # PROPERTIES ###########################################################
    @property
    def logger(self) -> Optional[Logger]:
        return self._logger

    @property
    def server(self) -> JSONRPCServer:
        return self._server
    
    @property
    def provider(self) -> str:
        return self._provider_name

    def __getitem__(self, item: str):
        """
        If the service exists, it is returned by its lookup key
        :param item: Key for looking up the service
        :raises RuntimeError: Service provider has not been initialized
        :return: The requested service
        """
        if not self._is_initialized:
            raise RuntimeError('Service provider must be initialized before retrieving services')

        return self._services[item]

    # METHODS ##############################################################

    def initialize(self) -> None:
        """
        Iterates over the services and initializes them with the server
        :raises RuntimeError: Service provider has been initialized already
        """
        if self._is_initialized:
            raise RuntimeError('Service provider cannot be initialized more than once')

        # Set initialized true before calling register, as otherwise services can't look each
        # other up. This is important since services can register callbacks with each other
        self._is_initialized = True

        for service_key in self._services:
            self._services[service_key].register(self)
