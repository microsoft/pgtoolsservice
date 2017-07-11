{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
ALTER TABLE {{ conn|qtIdent(data.schema, data.table) }}
    ADD{% if data.name %} CONSTRAINT {{ conn|qtIdent(data.name) }}{% endif%} FOREIGN KEY ({% for columnobj in data.columns %}{% if loop.index != 1 %}
, {% endif %}{{ conn|qtIdent(columnobj.local_column)}}{% endfor %})
    REFERENCES {{ conn|qtIdent(data.remote_schema, data.remote_table) }} ({% for columnobj in data.columns %}{% if loop.index != 1 %}
, {% endif %}{{ conn|qtIdent(columnobj.referenced)}}{% endfor %}) {% if data.confmatchtype %}MATCH FULL{% else %}MATCH SIMPLE{% endif%}

    ON UPDATE{% if data.confupdtype  == 'a' %}
 NO ACTION{% elif data.confupdtype  == 'r' %}
 RESTRICT{% elif data.confupdtype  == 'c' %}
 CASCADE{% elif data.confupdtype  == 'n' %}
 SET NULL{% elif data.confupdtype  == 'd' %}
 SET DEFAULT{% endif %}

    ON DELETE{% if data.confdeltype  == 'a' %}
 NO ACTION{% elif data.confdeltype  == 'r' %}
 RESTRICT{% elif data.confdeltype  == 'c' %}
 CASCADE{% elif data.confdeltype  == 'n' %}
 SET NULL{% elif data.confdeltype  == 'd' %}
 SET DEFAULT{% endif %}
{% if data.condeferrable %}

    DEFERRABLE{% if data.condeferred %}
 INITIALLY DEFERRED{% endif%}
{% endif%}
{% if data.convalidated %}

    NOT VALID{% endif%};
{% if data.comment and data.name %}

COMMENT ON CONSTRAINT {{ conn|qtIdent(data.name) }} ON {{ conn|qtIdent(data.schema, data.table) }}
    IS {{ data.comment|qtLiteral }};
{% endif %}