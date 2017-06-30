{#
 # pgAdmin 4 - PostgreSQL Tools
 #
 # Copyright (C) 2013 - 2017, The pgAdmin Development Team
 # This software is released under the PostgreSQL Licence
 #}
SELECT
	array_to_string(array_agg(sql), E'\n\n')
FROM
(SELECT
	CASE WHEN rolcanlogin THEN '-- User: ' ELSE '-- Role: ' END	||
		pg_catalog.quote_ident(rolname) ||
		E'\n-- DROP ' || CASE WHEN rolcanlogin THEN 'USER ' ELSE 'ROLE ' END ||
		pg_catalog.quote_ident(rolname) || E';\n\nCREATE ' ||
		CASE WHEN rolcanlogin THEN 'USER ' ELSE 'ROLE ' END ||
		pg_catalog.quote_ident(rolname) || E' WITH\n  ' ||
		CASE WHEN rolcanlogin THEN 'LOGIN' ELSE 'NOLOGIN' END || E'\n  ' ||
		CASE WHEN rolcanlogin AND rolpassword LIKE 'md5%%' THEN 'ENCRYPTED PASSWORD ' || quote_literal(rolpassword) || E'\n  ' ELSE '' END ||
		CASE WHEN rolsuper THEN 'SUPERUSER' ELSE 'NOSUPERUSER' END || E'\n  ' ||
		CASE WHEN rolinherit THEN 'INHERIT' ELSE 'NOINHERIT' END || E'\n  ' ||
		CASE WHEN rolcreatedb THEN 'CREATEDB' ELSE 'NOCREATEDB' END || E'\n  ' ||
		CASE WHEN rolcreaterole THEN 'CREATEROLE' ELSE 'NOCREATEROLE' END || E'\n  ' ||
		CASE WHEN rolconnlimit > 0 THEN E'\n  CONNECTION LIMIT ' || rolconnlimit ELSE '' END ||
		CASE WHEN rolvaliduntil IS NOT NULL THEN E'\n  VALID UNTIL ' || quote_literal(rolvaliduntil::text) ELSE ';' END ||
		-- PostgreSQL < 9.5
		CASE WHEN rolsuper AND NOT rolcatupdate THEN E'\n\nUPDATE pg_authid SET rolcatupdate=false WHERE rolname=' || pg_catalog.quote_literal(rolname) || ';' ELSE '' END AS sql
FROM
	pg_roles r
WHERE
	r.oid=%(rid)s::OID
UNION ALL
(SELECT
	array_to_string(array_agg(sql), E'\n')
FROM
(SELECT
	'GRANT ' || array_to_string(array_agg(rolname), ', ') || ' TO ' || pg_catalog.quote_ident(pg_get_userbyid(%(rid)s::OID)) ||
	CASE WHEN admin_option THEN ' WITH ADMIN OPTION;' ELSE ';' END AS sql
FROM
	(SELECT
		quote_ident(r.rolname) AS rolname, m.admin_option AS admin_option
	FROM
		pg_auth_members m
		LEFT JOIN pg_roles r ON (m.roleid = r.oid)
	WHERE
		m.member=%(rid)s::OID
	ORDER BY
		r.rolname
	) a
GROUP BY admin_option) s)
UNION ALL
(SELECT
	array_to_string(array_agg(sql), E'\n') AS sql
FROM
(SELECT
	'ALTER ' || CASE WHEN rolcanlogin THEN 'USER ' ELSE 'ROLE ' END || pg_catalog.quote_ident(rolname) || ' SET ' || param || ' TO ' || CASE WHEN param IN ('search_path', 'temp_tablespaces') THEN value ELSE quote_literal(value) END || ';' AS sql
FROM
(SELECT
	rolcanlogin, rolname, split_part(rolconfig, '=', 1) AS param, replace(rolconfig, split_part(rolconfig, '=', 1) || '=', '') AS value
FROM
	(SELECT
			unnest(rolconfig) AS rolconfig, rolcanlogin, rolname
	FROM
		pg_catalog.pg_roles
	WHERE
		oid=%(rid)s::OID
	) r
) a) b)
-- PostgreSQL >= 9.0
UNION ALL
(SELECT
	array_to_string(array_agg(sql), E'\n') AS sql
FROM
	(SELECT
		'ALTER ROLE ' || pg_catalog.quote_ident(pg_get_userbyid(%(rid)s::OID)) ||
		' IN DATABASE ' || pg_catalog.quote_ident(datname) ||
		' SET ' || param|| ' TO ' ||
		CASE
		WHEN param IN ('search_path', 'temp_tablespaces') THEN value
		ELSE quote_literal(value)
		END || ';' AS sql
	FROM
		(SELECT
			datname, split_part(rolconfig, '=', 1) AS param, replace(rolconfig, split_part(rolconfig, '=', 1) || '=', '') AS value
		FROM
			(SELECT
				d.datname, unnest(c.setconfig) AS rolconfig
			FROM
				(SELECT *
				FROM
					pg_catalog.pg_db_role_setting dr
				WHERE
					dr.setrole=%(rid)s::OID AND dr.setdatabase!=0) c
				LEFT JOIN pg_catalog.pg_database d ON (d.oid = c.setdatabase)
			) a
		) b
	) d
)
UNION ALL
(SELECT
	'COMMENT ON ROLE ' || pg_catalog.quote_ident(pg_get_userbyid(%(rid)s::OID)) || ' IS ' ||  pg_catalog.quote_literal(description) || ';' AS sql
FROM
	(SELECT	pg_catalog.shobj_description(%(rid)s::OID, 'pg_authid') AS description) a
WHERE
	description IS NOT NULL)) AS a
