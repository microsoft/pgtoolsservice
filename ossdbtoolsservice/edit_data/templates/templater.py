# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from abc import abstractmethod

DELETE_TEMPLATE = 'DELETE FROM {0} {1}'

WHERE_TEMPLATE = 'WHERE {0}'

SELECT_TEMPLATE = 'SELECT * FROM {0} {1}'

class Templater():
    """Abstract class that outlines SQL statement templates required for edit data."""

    # PROPERTIES ###########################################################
    @property
    def select_template(self) -> str:
        return SELECT_TEMPLATE
        
    @property
    def delete_template(self) -> str:
        return DELETE_TEMPLATE

    @property
    def where_template(self) -> str:
        return WHERE_TEMPLATE

    @property
    @abstractmethod
    def object_template(self) -> str:
        pass

    @property
    @abstractmethod
    def column_name_template(self) -> str:
        pass

    @property
    @abstractmethod
    def update_template(self) -> str:
        pass

    @property
    @abstractmethod
    def set_template(self) -> str:
        pass

    @property
    @abstractmethod
    def insert_template(self) -> str:
        pass
