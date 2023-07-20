{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% import 'security.macros' as SECLABEL %}
{% import 'privilege.macros' as PRIVILEGE %}
{% import 'variable.macros' as VARIABLE %}
{% set is_columns = [] %}
{% set exclude_quoting = ['search_path'] %}
{% if data %}
{% if query_for == 'sql_panel' and func_def is defined %}
CREATE OR REPLACE PROCEDURE {{func_def}}
{% else %}
CREATE{% if add_replace_clause %} OR REPLACE{% endif %} PROCEDURE {{ conn|qtIdent(data.pronamespace, data.name)|replace('"', '') }}{% if data.arguments is defined %}
({% for p in data.arguments %}{% if p.argmode %}{{p.argmode}} {% endif %}{% if p.argname %}{{ conn|qtIdent(p.argname)}} {% endif %}{% if p.argtype %}{{ p.argtype }}{% endif %}{% if p.argdefval %} DEFAULT {{p.argdefval}}{% endif %}
{% if not loop.last %}, {% endif %}
{% endfor -%}
{% endif %}
)
{% endif %}
LANGUAGE {{ data.lanname }}{% if data.prosecdef %}

    SECURITY DEFINER {% endif %}
{% if data.variables %}{% for v in data.variables %}

    SET {{ conn|qtIdent(v.name) }}={% if v.name in exclude_quoting %}{{ v.value }}{% else %}{{ v.value }}{% endif %}{% endfor -%}
{% endif %}

{% if data.is_pure_sql %}{{ data.prosrc }}
{% else %}
AS {% if data.lanname == 'c' %}
{{ data.probin }}, {{ data.prosrc_c }}
{% else %}
$BODY${{ data.prosrc }}$BODY${% endif -%};
{% endif -%}

{% if data.funcowner %}
ALTER PROCEDURE {{ conn|qtIdent(data.pronamespace, data.name)|replace('"', '') }}({{data.func_args}})
    OWNER TO {{ conn|qtIdent(data.funcowner) }};
{% endif -%}

{% if data.acl and not is_sql %}
{% for p in data.acl %}

{{ PRIVILEGE.SET(conn, "PROCEDURE", p.grantee, data.name, p.without_grant, p.with_grant, data.pronamespace, data.func_args)}}
{% endfor %}{% endif %}
{% if data.revoke_all %}

{{ PRIVILEGE.UNSETALL(conn, "PROCEDURE", "PUBLIC", data.name, data.pronamespace, data.func_args)}}
{% endif %}
{% if data.description %}

COMMENT ON PROCEDURE {{ conn|qtIdent(data.pronamespace, data.name)|replace('"', '') }}({{data.func_args}})
    IS {{ data.description  }};
{% endif -%}
{% if data.seclabels %}
{% for r in data.seclabels %}
{% if r.label and r.provider %}

{{ SECLABEL.SET(conn, 'PROCEDURE', data.name, r.provider, r.label, data.pronamespace, data.func_args) }}
{% endif %}
{% endfor %}
{% endif -%}

{% endif %}