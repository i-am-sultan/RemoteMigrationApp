CREATE EXTENSION DBLINK;
CREATE SERVER foreign_pgbase
    FOREIGN DATA WRAPPER dblink_fdw
    OPTIONS (dbname 'KTPL-DRILL', host 'psql-erp-stage-02.postgres.database.azure.com', port '5432');

ALTER SERVER foreign_pgbase
    OWNER TO gslpgadmin;
CREATE USER MAPPING FOR gslpgadmin SERVER foreign_pgbase
    OPTIONS (password 'gmpl', "user" 'gslpgadmin');
 

-- READONLY
GRANT USAGE ON SCHEMA main, public, gateway, ginview, ginarchive TO ginesys_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA main, public, gateway, ginview, ginarchive TO ginesys_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA main, public, gateway, ginview, ginarchive
GRANT SELECT ON TABLES TO ginesys_readonly;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA main, public, gateway, ginview, ginarchive TO ginesys_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA main, public, gateway, ginview, ginarchive
GRANT USAGE ON SEQUENCES TO ginesys_readonly;

-- READWRITE
GRANT USAGE, CREATE ON SCHEMA main, public, gateway, ginview, ginarchive TO ginesys_readwrite;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA main, public, gateway, ginview, ginarchive TO ginesys_readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA main, public, gateway, ginview, ginarchive 
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON TABLES TO ginesys_readwrite;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA main, public, gateway, ginview, ginarchive TO ginesys_readwrite;
ALTER DEFAULT PRIVILEGES IN SCHEMA main, public, gateway, ginview, ginarchive 
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO ginesys_readwrite;

-- DATABASE SPECIFIC
REVOKE ALL ON DATABASE "KTPL-DRILL" FROM public;
GRANT CONNECT ON DATABASE "KTPL-DRILL" TO ginesys_readonly_usr;
GRANT CONNECT ON DATABASE "KTPL-DRILL" TO ginesys_readwrite_usr;