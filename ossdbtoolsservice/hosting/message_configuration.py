from typing import Any, Generic, TypeVar

from pydantic import BaseModel

from ossdbtoolsservice.serialization.serializable import Serializable

# Generic type for parameters (BaseModel, Serializable or a plain dict)
TModel = TypeVar("TModel", bound=BaseModel | Serializable | dict[str, Any])


class IncomingMessageConfiguration(Generic[TModel]):
    """
    Stores info for registering a request (or notification).
    """

    message_configurations = []

    def __init__(self, method: str, parameter_class: type[TModel] | None) -> None:
        self.method = method
        self.parameter_class = parameter_class
        IncomingMessageConfiguration.message_configurations.append(self)


class OutgoingMessageRegistration:
    """
    Object to register outgoing message configuration.
    """

    message_configurations = []

    @staticmethod
    def register_outgoing_message(message_class: Any) -> None:
        OutgoingMessageRegistration.message_configurations.append(message_class)
