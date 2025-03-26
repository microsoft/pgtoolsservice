# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re
from typing import Optional

import smo.utils.templating as templating
from pgsmo.objects.server import server as s  # noqa
from smo.common.node_object import NodeCollection, NodeLazyPropertyCollection, NodeObject
from smo.common.scripting_mixins import ScriptableCreate, ScriptableDelete, ScriptableUpdate


class Column(NodeObject, ScriptableCreate, ScriptableDelete, ScriptableUpdate):
    TEMPLATE_ROOT = templating.get_template_root(__file__, "column")
    MACRO_ROOT = templating.get_template_root(__file__, "../table/macros")

    @classmethod
    def _from_node_query(cls, server: "s.Server", parent: NodeObject, **kwargs) -> "Column":
        """
        Creates a new Column object based on the the results from the column nodes query
        :param server: Server that owns the column
        :param parent: Parent object of the column. Should be a Table/View
        :param kwargs: Optional parameters for the column
        Kwargs:
            name str: Name of the column
            datatype str: Name of the type of the column
            oid int: Object ID of the column
            not_null bool: Whether or not null is allowed for the column
            has_default_value bool: Whether or not the column has a default value constraint
            isprimarykey bool: Whether or not the column is primary key
            is_updatable bool: Whether or not the column is updatable or read only
            isunique bool: Whether or not the column only accepts unique value or not
            default: default value for the column
        :return: Instance of the Column
        """

        col = cls(server, parent, kwargs["name"], kwargs["datatype"])
        col._oid = kwargs["oid"]
        col._has_default_value = kwargs["has_default_val"]
        col._not_null = kwargs["not_null"]
        col._column_ordinal = kwargs["oid"] - 1
        col._is_key = kwargs["isprimarykey"]
        col._is_readonly = kwargs["is_updatable"] is False
        col._is_unique = kwargs["isunique"]
        col._type_oid = kwargs["typoid"]
        col._default_value = kwargs["default"] if col._has_default_value is True else None
        col._is_auto_increment = (
            col._default_value is not None and col._default_value.startswith("nextval(")
        )

        return col

    def __init__(self, server: "s.Server", parent: NodeObject, name: str, datatype: str):
        """
        Initializes a new instance of a Column
        :param server: Connection to the server/database that this object will belong to
        :param parent: Parent object of the column, should be a Table/View
        :param name: Name of the column
        :param datatype: Type of the column
        """
        self._server = server
        self._parent: Optional[NodeObject] = parent
        self._name: str = name
        self._oid: Optional[int] = None
        self._is_system: bool = False

        self._child_collections: dict[str, NodeCollection] = {}
        self._property_collections: list[NodeLazyPropertyCollection] = []
        # Use _column_property_generator instead of _property_generator
        self._full_properties: NodeLazyPropertyCollection = (
            self._register_property_collection(self._column_property_generator)
        )

        ScriptableCreate.__init__(
            self, self._template_root(server), self._macro_root(), server.version
        )
        ScriptableDelete.__init__(
            self, self._template_root(server), self._macro_root(), server.version
        )
        ScriptableUpdate.__init__(
            self, self._template_root(server), self._macro_root(), server.version
        )

        self._datatype: str = datatype
        self._has_default_value: Optional[bool] = None
        self._not_null: Optional[bool] = None

        self._column_ordinal: int = None
        self._is_key: bool = None
        self._is_readonly: bool = None
        self._is_unique: bool = None
        self._type_oid: int = None
        self._default_value: Optional[str] = None
        self._is_auto_increment = None

    def _column_property_generator(self):
        template_root = self._template_root(self._server)

        # Setup the parameters for the query
        template_vars = self.template_vars

        # Render and execute the template
        sql = templating.render_template(
            templating.get_template_path(
                template_root, "properties.sql", self._server.version
            ),
            self._macro_root(),
            **template_vars,
        )
        cols, rows = self._server.connection.execute_dict(sql)

        for row in rows:
            if row["name"] == self._name:
                return row

    # PROPERTIES ###########################################################
    @property
    def datatype(self) -> str:
        return self._datatype

    @property
    def has_default_value(self) -> Optional[bool]:
        return self._has_default_value

    @property
    def not_null(self) -> Optional[bool]:
        return self._not_null

    @property
    def column_ordinal(self) -> int:
        return self._column_ordinal

    @property
    def is_key(self) -> bool:
        return self._is_key

    @property
    def is_readonly(self) -> bool:
        return self._is_readonly

    @property
    def is_unique(self) -> bool:
        return self._is_unique

    @property
    def type_oid(self) -> int:
        return self._type_oid

    @property
    def default_value(self) -> Optional[str]:
        return self._default_value

    @property
    def is_auto_increment(self) -> bool:
        return self._is_auto_increment

    @property
    def cltype(self):
        return self._full_properties["cltype"]

    @property
    def schema(self):
        return self._full_properties["schema"]

    @property
    def table(self):
        return self._full_properties["table"]

    @property
    def displaytypname(self):
        return self._full_properties["displaytypname"]

    @property
    def attlen(self):
        length, precision = self.get_length_precision(self.elemoid)
        if length:
            matchObj = re.search(r"(\d+)", self.fulltype)
            if matchObj:
                return matchObj.group(1)
        return None

    @property
    def elemoid(self):
        return self._full_properties["elemoid"]

    @property
    def attprecision(self):
        length, precision = self.get_length_precision(self.elemoid)
        if precision:
            matchObj = re.search(r"(\d+),(\d+)", self.fulltype)
            if matchObj:
                return matchObj.group(2)
        return precision

    @property
    def hasSqrBracket(self):
        return "[]" in self.cltype

    @property
    def fulltype(self):
        fulltype = self.get_full_type(
            self._full_properties["typnspname"],
            self._full_properties["typname"],
            self._full_properties["isdup"],
            self._full_properties["attndims"],
            self._full_properties["atttypmod"],
        )
        return fulltype

    @property
    def collspcname(self):
        return self._full_properties["collspcname"]

    @property
    def attnotnull(self):
        return self._full_properties["attnotnull"]

    @property
    def defval(self):
        return self._full_properties["defval"]

    @property
    def description(self):
        return self._full_properties["description"]

    @property
    def attoptions(self):
        return self._full_properties["attoptions"]

    @property
    def attacl(self):
        return self._full_properties["attacl"]

    @property
    def seclabels(self):
        return self._full_properties["seclabels"]

    @property
    def attstattarget(self):
        return self._full_properties["attstattarget"]

    @property
    def attstorage(self):
        return self._full_properties["attstorage"]

    @property
    def attidentity(self):
        return self._full_properties["attidentity"]

    @property
    def colconstype(self):
        return self._full_properties["colconstype"]

    @property
    def seqcache(self):
        return self._full_properties["seqcache"]

    @property
    def seqcycle(self):
        return self._full_properties["seqcycle"]

    @property
    def seqincrement(self):
        return self._full_properties["seqincrement"]

    @property
    def seqmax(self):
        return self._full_properties["seqmax"]

    @property
    def seqmin(self):
        return self._full_properties["seqmin"]

    @property
    def seqrelid(self):
        return self._full_properties["seqrelid"]

    @property
    def is_sql(self):
        return True

    # IMPLEMENTATION DETAILS ###############################################
    @classmethod
    def _macro_root(cls) -> list[str]:
        return [cls.MACRO_ROOT]

    @classmethod
    def _template_root(cls, server: "s.Server") -> str:
        return cls.TEMPLATE_ROOT

    @property
    def extended_vars(self):
        return {"tid": self.parent.oid}

    def _create_query_data(self) -> dict:
        """Provides data input for create script"""
        return {
            "data": {
                "name": self.name,
                "cltype": self.cltype,
                "schema": self.schema,
                "table": self.table,
                "displaytypname": self.displaytypname,
                "attlen": self.attlen,
                "attprecision": self.attprecision,
                "hasSqrBracket": self.hasSqrBracket,
                "collspcname": self.collspcname,
                "attnotnull": self.attnotnull,
                "defval": self.defval,
                "description": self.description,
                "attoptions": self.attoptions,
                "attacl": self.attacl,
                "seclabels": self.seclabels,
            },
            "is_sql": self.is_sql,
        }

    def _delete_query_data(self) -> dict:
        """Provides data input for delete script"""
        return {"data": {"schema": self.schema, "table": self.table, "name": self.name}}

    def _update_query_data(self) -> dict:
        """Function that returns data for update script"""
        return {
            "data": {
                "name": self.name,
                "schema": self.schema,
                "table": self.table,
                "cltype": self.cltype,
                "attlen": self.attlen,
                "attprecision": self.attprecision,
                "collspcname": self.collspcname,
                "defval": self.defval,
                "attnotnull": self.attnotnull,
                "attstattarget": self.attstattarget,
                "attstorage": self.attstorage,
                "description": self.description,
                "attoptions": self.attoptions,
                "attacl": self.attacl,
                "seclabels": self.seclabels,
            },
            "o_data": {
                "name": "",
                "cltype": "",
                "attlen": "",
                "attprecision": "",
                "collspcname": "",
                "defval": "",
                "attnotnull": "",
                "attstattarget": "",
                "attstorage": "",
            },
        }

    def get_length_precision(self, elemoid):
        precision = False
        length = False
        typeval = ""

        # Check against PGOID for specific type
        if elemoid:
            if elemoid in (1560, 1561, 1562, 1563, 1042, 1043, 1014, 1015):
                typeval = "L"
            elif elemoid in (1083, 1114, 1115, 1183, 1184, 1185, 1186, 1187, 1266, 1270):
                typeval = "D"
            elif elemoid in (1231, 1700):
                typeval = "P"
            else:
                typeval = " "

        # Set precision & length/min/max values
        if typeval == "P":
            precision = True

        if precision or typeval in ("L", "D"):
            length = True

        return length, precision


def get_full_type(self, nsp, typname, isDup, numdims, typmod):
    """
    Returns full type name with Length and Precision.

    Args:
        conn: Connection Object
        condition: condition to restrict SQL statement
    """
    schema = nsp if nsp is not None else ""
    name = ""
    array = ""
    length = ""

    # Above 7.4, format_type also sends the schema name if it's not included
    # in the search_path, so we need to skip it in the typname
    if typname.find(schema + '".') >= 0:
        name = typname[len(schema) + 3]
    elif typname.find(schema + ".") >= 0:
        name = typname[len(schema) + 1]
    else:
        name = typname

    if name.startswith("_"):
        if not numdims:
            numdims = 1
        name = name[1:]

    if name.endswith("[]"):
        if not numdims:
            numdims = 1
        name = name[:-2]

    if name.startswith('"') and name.endswith('"'):
        name = name[1:-1]

    if numdims > 0:
        while numdims:
            array += "[]"
            numdims -= 1

    if typmod != -1:
        length = "("
        if name == "numeric":
            _len = (typmod - 4) >> 16
            _prec = (typmod - 4) & 0xFFFF
            length += str(_len)
            if _prec:
                length += "," + str(_prec)
        elif (
            name == "time"
            or name == "timetz"
            or name == "time without time zone"
            or name == "time with time zone"
            or name == "timestamp"
            or name == "timestamptz"
            or name == "timestamp without time zone"
            or name == "timestamp with time zone"
            or name == "bit"
            or name == "bit varying"
            or name == "varbit"
        ):
            _prec = 0
            _len = typmod
            length += str(_len)
        elif name == "interval":
            _prec = 0
            _len = typmod & 0xFFFF
            length += str(_len)
        elif name == "date":
            # Clear length
            length = ""
        else:
            _len = typmod - 4
            _prec = 0
            length += str(_len)

        if len(length) > 0:
            length += ")"

    if name == "char" and schema == "pg_catalog":
        return '"char"' + array
    elif name == "time with time zone":
        return "time" + length + " with time zone" + array
    elif name == "time without time zone":
        return "time" + length + " without time zone" + array
    elif name == "timestamp with time zone":
        return "timestamp" + length + " with time zone" + array
    elif name == "timestamp without time zone":
        return "timestamp" + length + " without time zone" + array
    else:
        return name + length + array
