-- Truncate operations
TRUNCATE TABLE AUD_TABLE_DDL_LOG;
TRUNCATE TABLE AUD2_TABLE_DDL_LOG;
TRUNCATE TABLE Psite_Posapiconfig;
TRUNCATE TABLE Psite_webdb_configuration;

-- Update operations
UPDATE GDS2_Subscr SET webhookurl = NULL;
UPDATE GATEWAY.PACKDEF SET sw_licensedata = null, sw_licensestatus = null;

-- Create extension
CREATE EXTENSION DBLINK;

DO $$
DECLARE
    dbname text := current_database(); -- Current database name
    hostname text := inet_server_addr(); -- Current server's IP address
    port int := inet_server_port(); -- Current server's port
    username text := current_user; -- Current username
BEGIN
    -- Create foreign server
    EXECUTE format('
        CREATE SERVER foreign_pgbase
        FOREIGN DATA WRAPPER dblink_fdw
        OPTIONS (dbname ''%s'', host ''%s'', port ''%s'')',
        dbname, split_part(hostname, '/', 1), port);

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