
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import pgsqltoolsservice.utils as utils


class Serializable:
    @classmethod
    def from_dict(cls, dictionary: dict):
        kwargs = cls.get_child_serializable_types()
        ignore_extra_attributes = cls.ignore_extra_attributes()

        return utils.serialization.convert_from_dict(cls, dictionary, ignore_extra_attributes, **kwargs)

    @classmethod
    def get_child_serializable_types(cls):
        return {}

    @classmethod
    def ignore_extra_attributes(cls):
        return False
