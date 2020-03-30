{# FETCH properties for FTS CONFIGURATION #}
SELECT
    cfg.oid,
    cfg.cfgname as name,
    pg_get_userbyid(cfg.cfgowner) as owner,
    cfg.cfgparser as parser,
    cfg.cfgnamespace as schema,
    CASE WHEN (np.nspname not in ('public', 'pg_catalog') AND length(parser.prsname) > 0
    AND parser.prsname != 'default') THEN
        concat(quote_ident(np.nspname), '.', quote_ident(parser.prsname))
    ELSE parser.prsname END AS prsname,
    description
FROM
    pg_ts_config cfg
    LEFT OUTER JOIN pg_ts_parser parser
    ON parser.oid=cfg.cfgparser
    LEFT OUTER JOIN pg_description des
    ON (des.objoid=cfg.oid AND des.classoid='pg_ts_config'::regclass)
    LEFT OUTER JOIN pg_namespace np ON np.oid=parser.prsnamespace
WHERE
{% if scid %}
    cfg.cfgnamespace = {{scid}}::OID
{% endif %}
{% if name %}
    {% if scid %}AND {% endif %}cfg.cfgname = {{name|qtLiteral}}
{% endif %}
{% if cfgid %}
    {% if scid %}AND {% else %}{% if name %}AND {% endif %}{% endif %}cfg.oid = {{cfgid}}::OID
{% endif %}
ORDER BY cfg.cfgname
