import sys
import os
import logging
import socket
import argparse
import google_sheet as gsheet
import log_sheet as logsheet
import ora_pg_version_check as ora2pgversion
import connection_update as credupdate
import run_mig_app as migapp
import run_post_migration as postmig
import run_audit_app as runaudit
import run_post_mig_dblink_user as postmig2
import run_cube_population as cube
import run_create_jobs as jobs

# Configuration
MIGRATION_APP_PATH = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\RunEDBCommand.exe'
COMMON_POSTMIG_PATCH = r'C:\Program Files\edb\prodmig\PostMigPatches\postmigration.sql'
AUDIT_TRIGGER_APP_PATH = r'C:\Program Files\edb\prodmig\AuditTriggerCMDNew\netcoreapp3.1\TriggerConstraintViewCreationForAuditPostMigration.exe'

# Logging Configuration
LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, f'migration_log_{socket.gethostname()}.log')

logging.basicConfig(filename=LOG_FILE_PATH, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def update_status(sheet_ip, status_message):
    logsheet.update_sheet(sheet_ip, 'Status', status_message)
    logging.info(status_message)

def run_all_processes(credentials, private_ip, mode):
    try:
        # Process 1: Version Check
        version_check_result = ora2pgversion.compare_versions(credentials)
        if version_check_result:
            update_status(private_ip, f'{version_check_result}')
            return
        
        update_status(private_ip, 'DBVersion Matched')

        # Process 2: Credential Update
        cred_update_result = credupdate.update_connections(credentials)
        if cred_update_result:
            update_status(private_ip, f'{cred_update_result}')
            return
        
        update_status(private_ip, 'Credentials updated successfully.')

        # Process 3: Migration
        run_mig_result = migapp.run_mig_app(MIGRATION_APP_PATH)
        if run_mig_result:
            update_status(private_ip, f'{run_mig_result}')
            return
        
        update_status(private_ip, 'Migration app started successfully')
        migapp_status = migapp.check_run_mig_status(credentials)
        if migapp_status:
            update_status(private_ip, f'Migration failed! {migapp_status}')
            return
        
        update_status(private_ip, 'Migration succeeded! (with no row count mismatch).')

        # Process 4: Postmigration Script
        postmig_result = postmig.execute_postmigration_script(credentials, COMMON_POSTMIG_PATCH)
        if postmig_result:
            update_status(private_ip, f'Execution of postmigration failed. {postmig_result}')
            return
        
        update_status(private_ip, 'Postmigration Executed Successfully')

        # Process 5: Audit Trigger
        runaudit_result = runaudit.run_audit_app(AUDIT_TRIGGER_APP_PATH)
        if runaudit_result:
            update_status(private_ip, f'Execution of audittrigger app failed. {runaudit_result}')
            return
        
        update_status(private_ip, 'Audit trigger app executed successfully.')

        # Process 6: Postmigration Patch 2
        postmig2_result = postmig2.execute_sql_patch(credentials, 'drill')
        if postmig2_result:
            update_status(private_ip, f'Execution of dblink and user creation failed. {postmig2_result}')
            return
        
        update_status(private_ip, 'Postmigration patch 2(dblink, usermanagement) executed successfully')

        # Process 7: Cube Population
        cube_result = cube.run_cube_population(credentials)
        if cube_result:
            update_status(private_ip, f'Population of initial cube data failed. {cube_result}')
            return
        
        update_status(private_ip, 'Initial cube data populated successfully')

        # Process 8: Create Jobs (if drill mode)
        if mode == 'drill':
            jobs_result = jobs.create_database_jobs(credentials)
            if jobs_result:
                update_status(private_ip, f'Error while creating jobs {jobs_result}')
                return
            
            update_status(private_ip, 'Database jobs created successfully.')

    except Exception as e:
        update_status(private_ip, f'Error occurred: {str(e)}')
        logging.error(f'Error occurred: {str(e)}', exc_info=True)

def run_postmigration_and_audit(credentials, private_ip, mode):
    try:
        # Process 4: Postmigration Script
        postmig_result = postmig.execute_postmigration_script(credentials, COMMON_POSTMIG_PATCH)
        if postmig_result:
            update_status(private_ip, f'Execution of postmigration failed. {postmig_result}')
            return
        
        update_status(private_ip, 'Postmigration Executed Successfully')

        # Process 5: Audit Trigger
        runaudit_result = runaudit.run_audit_app(AUDIT_TRIGGER_APP_PATH)
        if runaudit_result:
            update_status(private_ip, f'Execution of audittrigger app failed. {runaudit_result}')
            return
        
        update_status(private_ip, 'Audit trigger app executed successfully.')

        # Process 6: Postmigration Patch 2
        postmig2_result = postmig2.execute_sql_patch(credentials, 'live')
        if postmig2_result:
            update_status(private_ip, f'Execution of dblink and user creation failed. {postmig2_result}')
            return
        
        update_status(private_ip, 'Postmigration patch 2(dblink, usermanagement) executed successfully')

        # Process 7: Cube Population
        cube_result = cube.run_cube_population(credentials)
        if cube_result:
            update_status(private_ip, f'Population of initial cube data failed. {cube_result}')
            return
        
        update_status(private_ip, 'Initial cube data populated successfully')

        # Process 8: Create Jobs (if drill mode)
        if mode == 'drill':
            jobs_result = jobs.create_database_jobs(credentials)
            if jobs_result:
                update_status(private_ip, f'Error while creating jobs {jobs_result}')
                return
            
            update_status(private_ip, 'Database jobs created successfully.')

    except Exception as e:
        update_status(private_ip, f'Error occurred: {str(e)}')
        logging.error(f'Error occurred: {str(e)}', exc_info=True)

def run_final_migration(credentials, private_ip, mode):
    try:
        # Process 6: Postmigration Patch 2
        postmig2_result = postmig2.execute_sql_patch(credentials, 'live')
        if postmig2_result:
            update_status(private_ip, f'Execution of dblink and user creation failed. {postmig2_result}')
            return
        
        update_status(private_ip, 'Postmigration patch 2(dblink, usermanagement) executed successfully')

        # Process 7: Cube Population
        cube_result = cube.run_cube_population(credentials)
        if cube_result:
            update_status(private_ip, f'Population of initial cube data failed. {cube_result}')
            return
        
        update_status(private_ip, 'Initial cube data populated successfully')

        # Process 8: Create Jobs (if drill mode)
        if mode == 'drill':
            jobs_result = jobs.create_database_jobs(credentials)
            if jobs_result:
                update_status(private_ip, f'Error while creating jobs {jobs_result}')
                return
            
            update_status(private_ip, 'Database jobs created successfully.')

    except Exception as e:
        update_status(private_ip, f'Error occurred: {str(e)}')
        logging.error(f'Error occurred: {str(e)}', exc_info=True)

def run_jobs(credentials):
    try:
        jobs_result = jobs.create_database_jobs(credentials)
        if jobs_result:
            update_status(private_ip, f'Error while creating jobs {jobs_result}')
            return
        
        update_status(private_ip, 'Database jobs created successfully.')

    except Exception as e:
        update_status(private_ip, f'Error occurred: {str(e)}')
        logging.error(f'Error occurred: {str(e)}', exc_info=True)

def parse_args():
    parser = argparse.ArgumentParser(description='Run migration and post-migration processes.')
    parser.add_argument('action', choices=['runall', 'runpostmig', 'runfinalmig', 'runjobs','application'], 
                        help='Action to perform')
    parser.add_argument('--mode', choices=['drill','live','update'],required=True, help='Optional mode for job creation')
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
        elif args.action == 'runjobs':
            run_jobs(credentials)
        elif args.action == 'applicaton':
            update_application()
        else:
            print('Wrong choice.')

    except Exception as e:
        logging.error(f'Unexpected error: {str(e)}', exc_info=True)
        sys.exit(1)