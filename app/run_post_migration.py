import psycopg2
import logging 
import os
import socket
from google_sheet import *
from log_sheet import *
import status_update
import json

common_postmig_patch = r'C:\Program Files\edb\prodmig\remote-mig-app\app\post-mig-patches\postmigration.sql'

# Logging Configuration
LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=LOG_FILE_PATH,filemode='a',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)

def execute_postmigration_script(credentials,patch_path):
    pgHost = credentials['pgHost']
    pgPort = credentials['pgPort']
    pgUserName = credentials['pgUser']
    pgPass = credentials['pgPass']
    pgDbname = credentials['pgDbName']

    connection = None
    cursor = None

    try:
        # Read the SQL patch file
        with open(patch_path, 'r') as f1:
            content = f1.read()

        # Connect to the PostgreSQL database
        connection = psycopg2.connect(database=pgDbname, user=pgUserName, password=pgPass, host=pgHost, port=pgPort)
        cursor = connection.cursor()
        cursor.execute(content)
        connection.commit()
    
        logging.info(f'Success: Postmigration {patch_path} executed on database {pgDbname}.')
        return 0

    except psycopg2.Error as e:
        # Log any psycopg2 database errors
        logging.info(f'\nError: Failed to execute postmigratoin {patch_path} on database {pgDbname}. Error: {e}')
        return f'\nError: Failed to execute postmigratoin {patch_path} on database {pgDbname}. Error: {e}'

    except Exception as e:
        # Log any other unexpected errors
        logging.info(f'\nError: Failed to execute postmigratoin {patch_path} on database {pgDbname}. Unexpected error: {e}')
        return f'\nError: Failed to execute postmigratoin {patch_path} on database {pgDbname}. Error: {e}'
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def check_postmigration_status(credentials):
    pgHost = credentials['pgHost']
    pgPort = credentials['pgPort']
    pgUserName = credentials['pgUser']
    pgPass = credentials['pgPass']
    pgDbname = credentials['pgDbName']

    connection = None
    cursor = None

    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(database=pgDbname, user=pgUserName, password=pgPass, host=pgHost, port=pgPort)
        cursor = connection.cursor()
        cursor.execute('select count(*) from ddl_failures')
        ddl_failure_count = cursor.fetchone()[0]
        connection.commit()
        logging.info(f'Postmigration status check successfull.')
        if ddl_failure_count:
            logging.info(f'Postmigration executed {ddl_failure_count}. \nWarning: Please check the ddl_failure table for the logs.')
            return f'Postmigration executed {ddl_failure_count}. Warning: Please check the ddl_failure table for the logs.'
        else:
            logging.info('No data found in table ddl_failure')
            return 0

    except psycopg2.Error as e:
        # Log any psycopg2 database errors
        logging.info(f'\nError: Failed to check post migration status on database {pgDbname}. Error: {e}')
        return f'\nError: Failed to check post migration status on database {pgDbname}. Error: {e}'

    except Exception as e:
        # Log any other unexpected errors
        logging.info(f'\nError: Failed to check post migration status on database  {pgDbname}. Unexpected error: {e}')
        return f'\nError: Failed to check post migration status on database  {pgDbname}. Error: {e}'
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


if __name__ == "__main__":
    current_user = os.getenv('USERNAME')
    status_file_path = f'C:\\Users\\{current_user}\\Desktop\\migration_status\\status.json'
    
    with open(status_file_path,'r') as status_file:
        status_content = json.load(status_file)
    if (status_content['Process'] == 'P3' and status_content['Status'] == 'O') or (status_content['Process'] == 'P3' and status_content['Status'] == 'F'):
        private_ip = get_private_ip()
        # excel_df = access_sheet()
        credentials = load_credentials_from_json(private_ip)
        postmig_result = execute_postmigration_script(credentials,common_postmig_patch)
        if postmig_result:
            status_update.update_status_in_file('P3','F',f'Execution of postmigration failed. {postmig_result}')
        else:
            postmig_status = check_postmigration_status(credentials)
            if postmig_status != 0:
                status_update.update_status_in_file_for_postmigration('P3','O','Postmigration Executed Successfully, Audit app started ...',postmig_status)
    else:
        logging.info('Process and Status is not matching to run run_post_migration.py')
