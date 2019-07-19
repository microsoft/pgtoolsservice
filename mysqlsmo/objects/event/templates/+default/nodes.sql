USE information_schema;

SELECT EVENT_NAME
FROM information_schema.EVENTS
WHERE TABLE_SCHEMA = '{{dbname}}';