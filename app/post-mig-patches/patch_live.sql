update gateway.packdef 
set sw_licensestatus = null,sw_licensedata = null;

CREATE EXTENSION DBLINK;

DO $$
DECLARE
    dbname text := current_database(); -- Current database name
    port int := inet_server_port(); -- Current server's port
    username text := current_user; -- Current username
BEGIN
    -- Create foreign server
    EXECUTE format('
        CREATE SERVER foreign_pgbase
        FOREIGN DATA WRAPPER dblink_fdw
        OPTIONS (dbname ''%s'', host ''psql-erp-stage-02.postgres.database.azure.com'', port ''%s'')',
        dbname, port);

    -- Alter server owner
    EXECUTE format('ALTER SERVER foreign_pgbase OWNER TO %I', username);

    -- Create user mapping
    CREATE USER MAPPING FOR gslpgadmin SERVER foreign_pgbase
        OPTIONS (password 'gmpl', "user" 'gslpgadmin');
END $$;
 

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
DO $$
DECLARE
    dbname text := current_database(); -- Current database name
BEGIN
    -- Alter server owner
    EXECUTE format('REVOKE ALL ON DATABASE "%s" FROM public;', dbname);
    EXECUTE format('GRANT CONNECT ON DATABASE "%s" TO ginesys_readonly_usr;', dbname);
    EXECUTE format('GRANT CONNECT ON DATABASE "%s" TO ginesys_readwrite_usr;', dbname);
END $$;