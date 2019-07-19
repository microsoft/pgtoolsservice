USE information_schema;

SELECT GRANTEE
FROM information_schema.USER_PRIVILEGES
GROUP BY GRANTEE;