USE information_schema;

SELECT TABLE_NAME
FROM information_schema.TABLES
WHERE TABLE_TYPE = 'VIEW' AND TABLE_SCHEMA = '{{dbname}}';