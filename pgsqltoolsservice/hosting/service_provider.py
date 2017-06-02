
from logging import Logger

from pgsqltoolsservice.hosting import JSONRPCServer


class ServiceProvider:
    def __init__(self, json_rpc_server: JSONRPCServer, logger: Logger):
        self._logger = logger
        self._server = json_rpc_server
        self._services = {}

    # PROPERTIES ###########################################################
    @property
    def logger(self) -> Logger:
        return self._logger

    @property
    def server(self) -> JSONRPCServer:
        return self._server

    # METHODS ##############################################################

    def get_service(self, name: str) -> any:
        """
        If the service exists, it is returned by its lookup key
        :param name: Key for looking up the service
        :return: The requested service
        """
        return self._services[name]

    def initialize(self) -> None:
        """
        Iterates over the services and initializes them with the server
        """
        for service_key in self._services:
            self._services[service_key].initialize()

    def set_service(self, name: str, service_class) -> None:
        """
        Adds a service to the service provider
        :param name: Key for looking up the service
        :param service_class:  Class of the service to instantiate and initialize
        """
        self._services[name] = service_class(self)
