import psycopg2
import logging 
import os
import socket
from google_sheet import *
from log_sheet import *

common_postmig_patch = r'C:\Program Files\edb\prodmig\PostMigPatches\postmigration.sql'

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
        return f'Success: Postmigration {patch_path} executed on database {pgDbname}.'

    except psycopg2.Error as e:
        # Log any psycopg2 database errors
        logging.info(f'\nError: Failed to execute postmigratoin {patch_path} on database {pgDbname}. Error: {e}')
        return f'\nError: Failed to execute postmigratoin {patch_path} on database {pgDbname}. Error: {e}'

    except Exception as e:
        # Log any other unexpected errors
        logging.info(f'\nError: Failed to execute postmigratoin {patch_path} on database {pgDbname}. Unexpected error: {e}')
        return f'\nError: Failed to execute postmigratoin {patch_path} on database {pgDbname}. Unexpected error: {e}'
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    private_ip = get_private_ip()
    excel_df = access_sheet()
    credentials = load_credentials_from_excel(excel_df,private_ip)
    result = execute_postmigration_script(credentials,common_postmig_patch)
    update_sheet(private_ip,'Status',result)