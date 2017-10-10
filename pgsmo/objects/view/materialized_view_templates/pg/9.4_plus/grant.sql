{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{# ===== Grant Permissions to User Role on Views/Tables ==== #}
{% import 'macros/schemas/security.macros' as SECLABEL %}
{% import 'macros/schemas/privilege.macros' as PRIVILEGE %}
{# We will generate Security Label SQL using macro #}
{% if data.seclabels %}{% for r in data.seclabels %}{{ SECLABEL.SET(conn, 'MATERIALIZED VIEW', data.name, r.provider, r.label, data.schema) }}{% endfor %}{% endif %}
{% if data.datacl %}{% for priv in data.datacl %}{{ PRIVILEGE.SET(conn, 'TABLE', priv.grantee, data.name, priv.without_grant, priv.with_grant, data.schema) }}{% endfor %}{% endif %}
