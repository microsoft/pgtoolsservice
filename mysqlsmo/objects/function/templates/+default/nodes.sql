USE information_schema;

SELECT ROUTINE_NAME
FROM information_schema.ROUTINES
WHERE ROUTINE_TYPE = 'FUNCTION' AND ROUTINE_SCHEMA = '{{dbname}}';