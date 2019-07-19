USE information_schema;

SELECT TRIGGER_NAME
FROM information_schema.TRIGGERS
WHERE TRIGGER_SCHEMA = '{{dbname}}' AND EVENT_OBJECT_TABLE='{{tbl_name}}';