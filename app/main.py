import sys
import os
import logging
import socket
import argparse
import json
import logging_config as logconf
import log_sheet as logsheet
import google_sheet as gsheet
import database_creation as createdb
import ora_pg_version_check as ora2pgversion
import connection_update as credupdate
import run_mig_app as migapp
import run_post_migration as postmig
import run_audit_app as runaudit
import run_post_mig_dblink_user as postmig2
import run_cube_population as cube
import run_create_jobs as jobs

# Configurationz
MIGRATION_APP_PATH = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\RunEDBCommand.exe'
COMMON_POSTMIG_PATCH = r'C:\Program Files\edb\prodmig\remote-mig-app\app\post-mig-patches\postmigration.sql'
AUDIT_TRIGGER_APP_PATH = r'C:\Program Files\edb\prodmig\AuditTriggerCMDNew\netcoreapp3.1\TriggerConstraintViewCreationForAuditPostMigration.exe'

def update_status(sheet_ip, status_message):
    logging.info(status_message)

def update_status_in_file(process_id, status, status_message):
    filepath = r'C:\Users\ginesysdevops\Desktop\migration_status\status.json'
    try:
        with open(filepath,'r') as file:
            content = json.load(file)
            content["Process"] = process_id
            content["Status"] = status
            content["Message"] = status_message
        with open(filepath,'w') as f:
            json.dump(content,f,indent=4)
        logging.info(f'Status updated in status.json')
    except FileNotFoundError:
        logging.error(f'Error: File {filepath} not found.')
    except json.JSONDecodeError as e:
        logging.error(f'Error decoding JSON from {filepath}: {e}', exc_info=True)
    except Exception as e:
        logging.error(f'Error updating config.json: {e}', exc_info=True)
    
def run_all_processes(credentials, private_ip, mode):
    try:
        # Process 0: Creation of database
        createdb_result = createdb.create_database(credentials,'templatedb')
        if createdb_result:
            update_status_in_file('P1','F',f'{createdb_result}')
            update_status(private_ip,f'{createdb_result}')
            return
        
        update_status_in_file('P1','O','Database setup done')
        update_status(private_ip,'Database setup done')

        # Process 1: Version Check
        version_check_result = ora2pgversion.compare_versions(credentials)
        if version_check_result:
            update_status_in_file('P1','F',f'{version_check_result}')
            update_status(private_ip, f'{version_check_result}')
            return
        
        update_status_in_file('P1','O','DBVersion Matched')
        update_status(private_ip, 'DBVersion Matched')

        # Process 2: Credential Update
        cred_update_result = credupdate.update_connections(credentials)
        if cred_update_result:
            update_status_in_file('P1','F',f'{cred_update_result}')
            update_status(private_ip,f'{cred_update_result}')
            return
        update_status_in_file('P1','O','Credentials updated successfully.')
        update_status(private_ip, 'Credentials updated successfully.')

        # Process 3: Migration
        run_mig_result = migapp.run_mig_app(MIGRATION_APP_PATH)
        if run_mig_result:
            update_status_in_file('P1','F',f'{run_mig_result}')
            update_status(private_ip, f'{run_mig_result}')
            return

        update_status_in_file('P1','O','Migration app started successfully.')
        update_status(private_ip, 'Migration app started successfully')
        migapp_status = migapp.check_run_mig_status(credentials)
        if migapp_status:
            update_status_in_file('P1','F', f'Migration failed! {migapp_status}')
            update_status(private_ip, f'Migration failed! {migapp_status}')
            return
        
        update_status_in_file('P2','O','Data migration succeeded! (with no row count mismatch).')        
        update_status(private_ip, 'Data migration succeeded! (with no row count mismatch).')

        # Process 4: Postmigration Script
        postmig_result = postmig.execute_postmigration_script(credentials, COMMON_POSTMIG_PATCH)
        if postmig_result:
            update_status_in_file('P2','F',f'Execution of postmigration failed. {postmig_result}')
            update_status(private_ip, f'Execution of postmigration failed. {postmig_result}')
            return
        
        update_status_in_file('P2','O','Postmigration Executed Successfully')        
        update_status(private_ip, 'Postmigration Executed Successfully')

        # Process 5: Audit Trigger
        runaudit_result = runaudit.run_audit_app(AUDIT_TRIGGER_APP_PATH)
        if runaudit_result:
            update_status_in_file('P2','F',f'Execution of audittrigger app failed. {runaudit_result}')
            update_status(private_ip, f'Execution of audittrigger app failed. {runaudit_result}')
            return
        
        update_status_in_file('P3','O','Audit trigger app executed successfully.')        
        update_status(private_ip, 'Audit trigger app executed successfully.')

        # Process 6: Postmigration Patch 2
        postmig2_result = postmig2.execute_sql_patch(credentials, 'drill')
        if postmig2_result:
            update_status_in_file('P3','F',f'Execution of dblink and user creation failed. {postmig2_result}')
            update_status(private_ip, f'Execution of dblink and user creation failed. {postmig2_result}')
            return
        
        update_status_in_file('P3','O','Postmigration patch 2(dblink, usermanagement) executed successfully')       
        update_status(private_ip, 'Postmigration patch 2(dblink, usermanagement) executed successfully')

        # Process 7: Cube Population
        cube_result = cube.run_cube_population(credentials)
        if cube_result:
            update_status_in_file('P3','F',f'Population of initial cube data failed. {cube_result}')
            update_status(private_ip, f'Population of initial cube data failed. {cube_result}')
            return
        update_status_in_file('P3','O','Initial cube data population started successfully.')       
        update_status(private_ip, 'Initial cube data population started successfully.')

        # Process 8: Create Jobs (if drill mode)
        if mode == 'drill':
            jobs_result = jobs.create_database_jobs(credentials)
            if jobs_result:
                update_status_in_file('P3','F',f'Error while creating jobs {jobs_result}')
                update_status(private_ip, f'Error while creating jobs {jobs_result}')
                return
            update_status_in_file('P4','S','Database jobs created successfully.')            
            update_status(private_ip, 'Database jobs created successfully.')
        update_status_in_file('P4','S','Initial cube data population started successfully.')       
        update_status(private_ip, 'Initial cube data population started successfully.')
    except Exception as e:
        update_status(private_ip, f'Error occurred: {str(e)}')
        logging.error(f'Error occurred: {str(e)}', exc_info=True)

def run_postmigration_and_audit(credentials, private_ip, mode):
    try:
        # Process 4: Postmigration Script
        postmig_result = postmig.execute_postmigration_script(credentials, COMMON_POSTMIG_PATCH)
        if postmig_result:
            update_status_in_file('P2','F',f'Execution of postmigration failed. {postmig_result}')
            update_status(private_ip, f'Execution of postmigration failed. {postmig_result}')
            return
        
        update_status_in_file('P2','O','Postmigration Executed Successfully')        
        update_status(private_ip, 'Postmigration Executed Successfully')

        # Process 5: Audit Trigger
        runaudit_result = runaudit.run_audit_app(AUDIT_TRIGGER_APP_PATH)
        if runaudit_result:
            update_status_in_file('P2','F',f'Execution of audittrigger app failed. {runaudit_result}')
            update_status(private_ip, f'Execution of audittrigger app failed. {runaudit_result}')
            return
        
        update_status_in_file('P3','O','Audit trigger app executed successfully.')        
        update_status(private_ip, 'Audit trigger app executed successfully.')

        # Process 6: Postmigration Patch 2
        postmig2_result = postmig2.execute_sql_patch(credentials, 'drill')
        if postmig2_result:
            update_status_in_file('P3','F',f'Execution of dblink and user creation failed. {postmig2_result}')
            update_status(private_ip, f'Execution of dblink and user creation failed. {postmig2_result}')
            return
        
        update_status_in_file('P3','O','Postmigration patch 2(dblink, usermanagement) executed successfully')       
        update_status(private_ip, 'Postmigration patch 2(dblink, usermanagement) executed successfully')

        # Process 7: Cube Population
        cube_result = cube.run_cube_population(credentials)
        if cube_result:
            update_status_in_file('P3','F',f'Population of initial cube data failed. {cube_result}')
            update_status(private_ip, f'Population of initial cube data failed. {cube_result}')
            return
        update_status_in_file('P3','O','Initial cube data population started successfully.')       
        update_status(private_ip, 'Initial cube data population started successfully.')

        # Process 8: Create Jobs (if drill mode)
        if mode == 'drill':
            jobs_result = jobs.create_database_jobs(credentials)
            if jobs_result:
                update_status_in_file('P3','F',f'Error while creating jobs {jobs_result}')
                update_status(private_ip, f'Error while creating jobs {jobs_result}')
                return
            update_status_in_file('P4','S','Database jobs created successfully.')            
            update_status(private_ip, 'Database jobs created successfully.')

        update_status_in_file('P4','S','Initial cube data population started successfully.')       
        update_status(private_ip, 'Initial cube data population started successfully.')

    except Exception as e:
        update_status(private_ip, f'Error occurred: {str(e)}')
        logging.error(f'Error occurred: {str(e)}', exc_info=True)

def run_final_migration(credentials, private_ip, mode):
    try:
        # Process 6: Postmigration Patch 2
        postmig2_result = postmig2.execute_sql_patch(credentials, 'drill')
        if postmig2_result:
            update_status_in_file('P3','F',f'Execution of dblink and user creation failed. {postmig2_result}')
            update_status(private_ip, f'Execution of dblink and user creation failed. {postmig2_result}')
            return
        
        update_status_in_file('P3','O','Postmigration patch 2(dblink, usermanagement) executed successfully')       
        update_status(private_ip, 'Postmigration patch 2(dblink, usermanagement) executed successfully')

        # Process 7: Cube Population
        cube_result = cube.run_cube_population(credentials)
        if cube_result:
            update_status_in_file('P3','F',f'Population of initial cube data failed. {cube_result}')
            update_status(private_ip, f'Population of initial cube data failed. {cube_result}')
            return
        update_status_in_file('P3','O','Initial cube data population started successfully.')       
        update_status(private_ip, 'Initial cube data population started successfully.')

        # Process 8: Create Jobs (if drill mode)
        if mode == 'drill':
            jobs_result = jobs.create_database_jobs(credentials)
            if jobs_result:
                update_status_in_file('P3','F',f'Error while creating jobs {jobs_result}')
                update_status(private_ip, f'Error while creating jobs {jobs_result}')
                return
            update_status_in_file('P4','S','Database jobs created successfully.')            
            update_status(private_ip, 'Database jobs created successfully.')
        update_status_in_file('P4','S','Initial cube data population started successfully.')       
        update_status(private_ip, 'Initial cube data population started successfully.')
    except Exception as e:
        update_status(private_ip, f'Error occurred: {str(e)}')
        logging.error(f'Error occurred: {str(e)}', exc_info=True)
'''
def run_jobs(credentials):
    try:
        jobs_result = jobs.create_database_jobs(credentials)
        if jobs_result:
            update_status_in_file('P4','F',f'Error while creating jobs {jobs_result}')
            update_status(private_ip, f'Error while creating jobs {jobs_result}')
            return
        update_status_in_file('P4','S','Database jobs created successfully.')            
        update_status(private_ip, 'Database jobs created successfully.')
        
    except Exception as e:
        update_status(private_ip, f'Error occurred: {str(e)}')
        logging.error(f'Error occurred: {str(e)}', exc_info=True)
'''
def parse_args():
    parser = argparse.ArgumentParser(description='Run migration and post-migration processes.')
    parser.add_argument('action', choices=['runall', 'runpostmig', 'runfinalmig'], 
                        help='Action to perform')
    parser.add_argument('--mode', choices=['drill','live'],required=True, help='Optional mode for job creation')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    try:
        private_ip = gsheet.get_private_ip()
        all_credentials = gsheet.access_sheet()
        credentials = gsheet.load_credentials_from_excel(all_credentials, private_ip)
        
        if args.action == 'runall':
            run_all_processes(credentials, private_ip, args.mode)
        elif args.action == 'runpostmig':
            run_postmigration_and_audit(credentials, private_ip, args.mode)
        elif args.action == 'runfinalmig':
            run_final_migration(credentials, private_ip, args.mode)
        # elif args.action == 'runjobs':
        #     run_jobs(credentials)
        else:
            print('Wrong choice.')

    except Exception as e:
        logging.error(f'Unexpected error: {str(e)}', exc_info=True)
        sys.exit(1)