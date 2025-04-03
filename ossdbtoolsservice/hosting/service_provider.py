# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from abc import ABC, abstractmethod
from logging import Logger
from typing import Any, Optional, TypeVar

from ossdbtoolsservice.hosting.message_server import MessageServer
from ossdbtoolsservice.utils import constants

S = TypeVar("S", bound="Service")


class Service(ABC):
    def __init__(self) -> None:
        self._service_provider: ServiceProvider | None = None

    @abstractmethod
    def register(self, service_provider: "ServiceProvider") -> None:
        pass

    @property
    def service_provider(self) -> "ServiceProvider":
        if self._service_provider is None:
            raise ValueError("Service provider is not set")
        return self._service_provider

    @property
    def server(self) -> MessageServer:
        if self.service_provider is None:
            raise ValueError("Service provider is not set")
        if self.service_provider.server is None:
            raise ValueError("Message server is not set")
        return self.service_provider.server

    def shutdown(self) -> None:  # noqa: B027
        """
        Called when the service provider is shutting
        down. This is a good place to clean up any resources
        that the service is using. Default implementation does nothing.
        """
        pass

    def _log_warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.service_provider and self.service_provider.logger:
            self.service_provider.logger.warning(msg, *args, **kwargs)

    def _log_error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.service_provider and self.service_provider.logger:
            self.service_provider.logger.error(msg, *args, **kwargs)

    def _log_info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.service_provider and self.service_provider.logger:
            self.service_provider.logger.info(msg, *args, **kwargs)

    def _log_debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.service_provider and self.service_provider.logger:
            self.service_provider.logger.debug(msg, *args, **kwargs)

    def _log_exception(self, msg: str | Exception, *args: Any, **kwargs: Any) -> None:
        if self.service_provider and self.service_provider.logger:
            self.service_provider.logger.exception(msg, *args, **kwargs)


class ServiceProvider:
    def __init__(
        self,
        message_server: MessageServer,
        services: dict[str, type[Service] | Service],
        logger: Optional[Logger] = None,
    ):
        self._is_initialized = False
        self._logger = logger
        self._server = message_server
        self._provider_name = constants.PG_PROVIDER_NAME
        self._services = {
            service_name: service_class()
            if isinstance(service_class, type)
            else service_class
            for (service_name, service_class) in services.items()
        }

    # PROPERTIES ###########################################################

    @property
    def logger(self) -> Optional[Logger]:
        return self._logger

    @property
    def server(self) -> MessageServer:
        return self._server

    @property
    def provider(self) -> str:
        return self._provider_name

    def __getitem__(self, item: str) -> Service:
        """
        If the service exists, it is returned by its lookup key
        :param item: Key for looking up the service
        :raises RuntimeError: Service provider has not been initialized
        :return: The requested service
        """
        if not self._is_initialized:
            raise RuntimeError(
                "Service provider must be initialized before retrieving services"
            )

        return self._services[item]

    def get(self, item: str, class_: type[S]) -> S:
        """
        If the service exists, it is returned by its lookup key
        :param item: Key for looking up the service
        :raises RuntimeError: Service provider has not been initialized
        :return: The requested service
        """
        if not self._is_initialized:
            raise RuntimeError(
                "Service provider must be initialized before retrieving services"
            )

        if item not in self._services:
            raise KeyError(f"Service '{item}' not found")

        service = self._services[item]
        if not isinstance(service, class_):
            raise TypeError(f"Service '{item}' is not of type {class_.__name__}")
        return service

    def __enter__(self) -> "ServiceProvider":
        """
        Context manager for the service provider
        :return: The service provider
        """
        self.initialize()
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[Exception],
        traceback: Optional[Any],
    ) -> None:
        for service in self._services.values():
            service.shutdown()

    # METHODS ##############################################################

    def initialize(self) -> None:
        """
        Iterates over the services and initializes them with the server
        :raises RuntimeError: Service provider has been initialized already
        """
        if self._is_initialized:
            raise RuntimeError("Service provider cannot be initialized more than once")

        # Set initialized true before calling register, as otherwise services can't look each
        # other up. This is important since services can register callbacks with each other
        self._is_initialized = True

        for service_key in self._services:
            self._services[service_key].register(self)
