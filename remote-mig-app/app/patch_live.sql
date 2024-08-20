CREATE EXTENSION DBLINK;
CREATE SERVER foreign_pgbase
    FOREIGN DATA WRAPPER dblink_fdw
    OPTIONS (dbname 'STARTRON-PROD', host 'psql-erp-stage-02.postgres.database.azure.com', port '5432');

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
REVOKE ALL ON DATABASE "STARTRON-PROD" FROM public;
GRANT CONNECT ON DATABASE "STARTRON-PROD" TO ginesys_readonly_usr;
GRANT CONNECT ON DATABASE "STARTRON-PROD" TO ginesys_readwrite_usr;
/*
call populate_first_time_migdata(); 

call main.db_pro_sitetositemovement_firsttimepopulation_outward('2023-04-01', CURRENT_DATE);
call main.db_pro_sitetositemovement_firsttimepopulation_inward('2023-04-01', CURRENT_DATE);
call main.db_pro_sitetositemovement_not_in_outward();
call main.db_proc_sitetosite_intransum('2023-04-01'); --start DATE
--FOR COMPOSITE_GST:
call main.db_pro_compositegst_firsttimepopulation('2023-04-01', CURRENT_DATE);
--FOR STOCK BOOK SUMMARY:
call main.db_pro_stk_bk_summary_master_build('2023-04-01');
call db_pro_stk_ageing_firsttime();
*/