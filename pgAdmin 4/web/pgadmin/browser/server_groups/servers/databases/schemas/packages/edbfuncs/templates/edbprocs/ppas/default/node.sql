SELECT  pg_proc.oid,
        pg_proc.proname || '(' || COALESCE(pg_catalog.pg_get_function_identity_arguments(pg_proc.oid), '') || ')' AS name,
        pg_get_userbyid(proowner) AS funcowner
FROM pg_proc, pg_namespace
WHERE protype = '1'::char
{% if fnid %}
AND pg_proc.oid = {{ fnid|qtLiteral }}
{% endif %}
AND pronamespace = {{pkgid|qtLiteral}}::oid
AND pg_proc.pronamespace = pg_namespace.oid
