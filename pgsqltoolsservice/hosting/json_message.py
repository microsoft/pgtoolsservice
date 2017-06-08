# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from enum import Enum
import inflection


class JSONRPCMessageType(Enum):
    Request = 1
    ResponseSuccess = 2
    ResponseError = 3
    Notification = 4


class JSONRPCMessage:
    """
    Internal representation of a JSON RPC message. Provides logic for converting back and forth
    from dictionary
    """

    # CONSTRUCTORS #########################################################
    @classmethod
    def create_error(cls, msg_id, code, message, data):
        error = {
            'code': code,
            'message': message,
            'data': data
        }
        return cls(JSONRPCMessageType.ResponseError, msg_id=msg_id, msg_error=error)

    @classmethod
    def create_notification(cls, method, params):
        return cls(JSONRPCMessageType.Notification, msg_method=method, msg_params=params)

    @classmethod
    def create_request(cls, msg_id, method, params):
        return cls(JSONRPCMessageType.Request, msg_id=msg_id, msg_method=method, msg_params=params)

    @classmethod
    def create_response(cls, msg_id, result):
        return cls(JSONRPCMessageType.ResponseSuccess, msg_id=msg_id, msg_result=result)

    @classmethod
    def from_dictionary(cls, msg_dict):
        """
        Decomposes a dictionary from a JSON RPC message into components with light validation
        :param msg_dict: Dictionary of components from deserializing a JSON RPC message
        :return: JsonRpcMessage that is setup as per the dictionary
        """
        # Read all the possible values in from the message dictionary
        # If the keys don't exist in the dict, then None is set, which is acceptable
        msg_id = msg_dict.get('id')
        msg_method = msg_dict.get('method')
        msg_params = msg_dict.get('params')
        msg_result = msg_dict.get('result')
        msg_error = msg_dict.get('error')

        if msg_id is None:
            # Messages that lack an id are notifications
            if msg_method is None:
                raise ValueError('Notification message is missing method')
            msg_type = JSONRPCMessageType.Notification

        else:
            # Message has id, therefore it is a response or a request
            if msg_result is not None:
                # A result field indicates this is a successful response
                msg_type = JSONRPCMessageType.ResponseSuccess
            elif msg_error is not None:
                # An error field indicated this is a failure response
                msg_type = JSONRPCMessageType.ResponseError
            else:
                # Lack of a result or error field indicates a request message
                if msg_method is None:
                    raise ValueError("Request message is missing method")
                msg_type = JSONRPCMessageType.Request

        return cls(msg_type, msg_id, msg_method, msg_params, msg_result, msg_error)

    def __init__(self, msg_type,
                 msg_id=None,
                 msg_method=None,
                 msg_params=None,
                 msg_result=None,
                 msg_error=None):
        self._message_type = msg_type
        self._message_id = msg_id
        self._message_method = msg_method
        self._message_params = msg_params
        self._message_result = msg_result
        self._message_error = msg_error

    # PROPERTIES ###########################################################
    @property
    def message_id(self):
        return self._message_id

    @property
    def message_method(self):
        return self._message_method

    @property
    def message_params(self):
        return self._message_params

    @property
    def message_result(self):
        return self._message_result

    @property
    def message_error(self):
        return self._message_error

    @property
    def message_type(self):
        return self._message_type

    @property
    def dictionary(self):
        message_base = {'jsonrpc': '2.0'}

        if self._message_type is JSONRPCMessageType.Request:
            message_base['method'] = self._message_method
            message_base['params'] = self._serialize_to_dict(self._message_params)
            message_base['id'] = self._message_id
            return message_base

        if self._message_type is JSONRPCMessageType.ResponseSuccess:
            message_base['result'] = self._serialize_to_dict(self._message_result)
            message_base['id'] = self._message_id
            return message_base

        if self._message_type is JSONRPCMessageType.Notification:
            message_base['method'] = self._serialize_to_dict(self._message_method)
            message_base['params'] = self._message_params
            return message_base

        if self._message_type is JSONRPCMessageType.ResponseError:
            message_base['error'] = self._serialize_to_dict(self._message_error)
            message_base['id'] = self._message_id
            return message_base

    # METHODS ##############################################################

    def __eq__(self, other):
        """
        Performs comparison of two messages to see if their contents are the same.
        Primarily provided for unit testing
        :param other: Message to compare against
        :return: True if the dictionary representations are the same, False otherwise
        """
        return self.dictionary == other.dictionary

    def __ne__(self, other):
        """
        Performs comparison of two messages to see if their contents are not the same.
        Primarily provided for unit testing
        :param other: Message to compare against
        :return: True if the dictionary representations are not the same, False otherwise
        """
        return not self == other

    # IMPLEMENTATION DETAILS ###############################################

    def _serialize_to_dict(self, obj):
        """
        Serializes an object to a json-ready dictionary using attribute name normalization. The
        serialization is repeated, recursively until a built-in type is returned
        :param obj: The object to convert to a jsonic dictionary
        :return: A json-ready dictionary representation of the object
        """
        # Look for __dict__ or __slots__ in the object
        if not (hasattr(obj, '__dict__') or hasattr(obj, '__slots__')):
            # Object is a built-in. Don't process it.
            return obj

        # Object is not a built-in, so process its dictionary/slots
        attrs = []
        try:
            # __dict__ is default, so try that first
            attrs = obj.__dict__
        except NameError:
            # __slots__ will work too, so try that next
            attrs = obj.__slots__

        # Iterate over the objects, recursively call and store the output as a camelCase output
        output = {}
        for attr in attrs:
            jsonic_attr = inflection.camelize(attr, False)
            output[jsonic_attr] = self._serialize_to_dict(getattr(obj, attr))

        return output
