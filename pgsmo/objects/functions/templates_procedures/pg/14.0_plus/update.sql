{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
{% import 'security.macros' as SECLABEL %}
{% import 'privilege.macros' as PRIVILEGE %}
{% import 'variable.macros' as VARIABLE %}{% if data %}
{% set name = o_data.name %}
{% set exclude_quoting = ['search_path'] %}
{% if data.name %}
{% if data.name != o_data.name %}
ALTER PROCEDURE {{ conn|qtIdent(o_data.pronamespace, o_data.name) }}{% if o_data.proargtypenames %}({{ o_data.proargtypenames }}){% endif %}

    RENAME TO {{ conn|qtIdent(data.name) }};
{% set name = data.name %}
{% endif %}

{% endif -%}
{% if data.change_func  %}
CREATE OR REPLACE PROCEDURE {{ conn|qtIdent(o_data.pronamespace, name) }}({% if data.arguments %}{% for p in data.arguments %}{% if p.argmode %}{{p.argmode}} {% endif %}{% if p.argname %}{{ conn|qtIdent(p.argname) }} {% endif %}{% if p.argtype %}{{ p.argtype }}{% endif %}{% if p.argdefval %} DEFAULT {{p.argdefval}}{% endif %}
{% if not loop.last %}, {% endif %}
{% endfor %}
{% endif %}
)
{% if 'lanname' in data %}
    LANGUAGE {{ data.lanname }} {% else %}
    LANGUAGE {{ o_data.lanname }}
    {% endif %}
{% if ('prosecdef' in data and data.prosecdef) or ('prosecdef' not in data and o_data.prosecdef) %}SECURITY DEFINER{% endif %}
{% if data.merged_variables %}{% for v in data.merged_variables %}

    SET {{ conn|qtIdent(v.name) }}={% if v.name in exclude_quoting %}{{ v.value }}{% else %}{{ v.value }}{% endif %}{% endfor -%}
{% endif %}

{% if data.is_pure_sql %}{{ data.prosrc }}{% else %}
AS {% if (data.lanname == 'c' or o_data.lanname == 'c') and ('probin' in data or 'prosrc_c' in data) %}
{% if 'probin' in data %}{{ data.probin }}{% else %}{{ o_data.probin }}{% endif %}, {% if 'prosrc_c' in data %}{{ data.prosrc_c }}{% else %}{{ o_data.prosrc_c }}{% endif %}{% elif 'prosrc' in data %}
$BODY${{ data.prosrc }}$BODY${% elif o_data.lanname == 'c' %}
{{ o_data.probin }}, {{ o_data.prosrc_c }}{% else %}
$BODY${{ o_data.prosrc }}$BODY${% endif -%};
{% endif -%}
{% endif -%}
{% if data.funcowner %}

ALTER PROCEDURE {{ conn|qtIdent(o_data.pronamespace, name) }}{% if o_data.proargtypenames %}({{ o_data.proargtypenames }}){% endif %}
    OWNER TO {{ conn|qtIdent(data.funcowner) }};
{% endif -%}
{# The SQL generated below will change priviledges #}
{% if data.acl %}
{% if 'deleted' in data.acl %}
{% for priv in data.acl.deleted %}

{{ PRIVILEGE.UNSETALL(conn, 'PROCEDURE', priv.grantee, name, o_data.pronamespace, o_data.proargtypenames) }}
{% endfor %}
{% endif -%}
{% if 'changed' in data.acl %}
{% for priv in data.acl.changed %}

{% if priv.grantee != priv.old_grantee %}
{{ PRIVILEGE.UNSETALL(conn, 'PROCEDURE', priv.old_grantee, name, o_data.pronamespace, o_data.proargtypenames) }}
{% else %}
{{ PRIVILEGE.UNSETALL(conn, 'PROCEDURE', priv.grantee, name, o_data.pronamespace, o_data.proargtypenames) }}
{% endif %}

{{ PRIVILEGE.SET(conn, 'PROCEDURE', priv.grantee, name, priv.without_grant,
 priv.with_grant, o_data.pronamespace, o_data.proargtypenames) }}
{% endfor %}
{% endif -%}
{% if 'added' in data.acl %}
{% for priv in data.acl.added %}

{{ PRIVILEGE.SET(conn, 'PROCEDURE', priv.grantee, name, priv.without_grant, priv.with_grant, o_data.pronamespace, o_data.proargtypenames) }}
{% endfor %}
{% endif %}
{% endif -%}
{% if data.change_func == False %}
{% if data.variables %}
{% if 'deleted' in data.variables and data.variables.deleted|length > 0 %}

{{ VARIABLE.UNSET(conn, 'PROCEDURE', name, data.variables.deleted, o_data.pronamespace, o_data.proargtypenames) }}
{% endif -%}
{% if 'merged_variables' in data and data.merged_variables|length > 0 %}

{{ VARIABLE.SET(conn, 'PROCEDURE', name, data.merged_variables, o_data.pronamespace, o_data.proargtypenames) }}
{% endif -%}
{% endif -%}
{% endif -%}
{% set seclabels = data.seclabels %}
{% if 'deleted' in seclabels and seclabels.deleted|length > 0 %}
{% for r in seclabels.deleted %}

{{ SECLABEL.UNSET(conn, 'PROCEDURE', name, r.provider, o_data.pronamespace, o_data.proargtypenames) }}
{% endfor %}
{% endif -%}
{% if 'added' in seclabels and seclabels.added|length > 0 %}
{% for r in seclabels.added %}

{{ SECLABEL.SET(conn, 'PROCEDURE', name, r.provider, r.label, o_data.pronamespace, o_data.proargtypenames) }}
{% endfor %}
{% endif -%}
{% if 'changed' in seclabels and seclabels.changed|length > 0 %}
{% for r in seclabels.changed %}

{{ SECLABEL.SET(conn, 'PROCEDURE', name, r.provider, r.label, o_data.pronamespace, o_data.proargtypenames) }}
{% endfor %}
{% endif -%}
{% if data.description is defined and data.description != o_data.description%}

COMMENT ON PROCEDURE {{ conn|qtIdent(o_data.pronamespace, name) }}({{o_data.proargtypenames }})
    IS {{ data.description }};
{% endif -%}
{% if data.pronamespace %}

ALTER PROCEDURE {{ conn|qtIdent(o_data.pronamespace, name) }}
    SET SCHEMA {{ conn|qtIdent(data.pronamespace) }};
{% endif -%}

{% endif %}