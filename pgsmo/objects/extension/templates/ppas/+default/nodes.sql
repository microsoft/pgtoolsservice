{# ======================Fetch extensions names=====================#}
{% import 'systemobjects.macros' as SYSOBJECTS %}
SELECT
    a.name, a.installed_version,
    array_agg(av.version) as version,
    nsp.nspname as schema,
    array_agg(av.superuser) as superuser,
    array_agg(av.relocatable) as relocatable,
    nsp.oid AS schemaoid,
    px.oid as oid,
    {{ SYSOBJECTS.IS_SYSTEMSCHEMA('nsp') }} as is_system
FROM
    pg_available_extensions a
    LEFT JOIN pg_available_extension_versions av ON (a.name = av.name)
    LEFT JOIN pg_extension px on px.extname=a.name
    INNER JOIN pg_namespace nsp ON px.extnamespace = nsp.oid
GROUP BY a.name, a.installed_version,nsp.oid,px.oid,nsp.nspname,{{ SYSOBJECTS.IS_SYSTEMSCHEMA('nsp') }}
ORDER BY nsp.nspname, a.name 


