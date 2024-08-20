import psycopg2
import logging 
import os
import socket
from google_sheet import *
from log_sheet import *
import sys
import status_update
import json

# Logging Configuration
LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=LOG_FILE_PATH, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def create_database_jobs(credentials):
    pgHost = credentials['pgHost']
    pgPort = credentials['pgPort']
    pgUserName = credentials['pgUser']
    pgPass = credentials['pgPass']
    pgDbname = credentials['pgDbName']

    connection = None
    cursor = None
    try:
        # Connect to the PostgreSQL database and execute the job creation procedure.
        connection = psycopg2.connect(database='postgres', user=pgUserName, password=pgPass, host=pgHost, port=pgPort)
        cursor = connection.cursor()
        cursor.execute('call schedule_jobs_in_postgres()')
        connection.commit()
        logging.info(f'\nSuccessfully created jobs for the database {pgDbname}.')
        return f'\nSuccessfully created jobs for the database {pgDbname}.'
    except psycopg2.Error as e:
        logging.info(f'\nError creating jobs for the database {pgDbname}: {e}')
        return f'\nError creating jobs for the database {pgDbname}: {e}'
    except Exception as e:
        logging.info(f'\nUnexpected error while creating jobs for the database {pgDbname}: {e}')
        return f'\nUnexpected error while creating jobs for the database {pgDbname}: {e}'
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    status_file_path = r'C:\Users\ginesysdevops\Desktop\migration_status\status.json'
    with open(status_file_path,'r') as status_file:
        status_content = json.load(status_file)
    if status_content['Process'] == 'P4' and status_content['Status'] == 'O':
        private_ip = get_private_ip()
        excel_df = access_sheet()
        credentials = load_credentials_from_excel(excel_df,private_ip)
        if sys.argv[1] == 'drill':
            jobs_result = create_database_jobs(credentials)
            if jobs_result:
                status_update.update_status_in_file('P4','F',f'Error while creating jobs {jobs_result}')
            else:
                status_update.update_status_in_file('P4','S','Migration completed (Database jobs created.)')   
        elif sys.argv[1] == 'live':
            status_update.update_status_in_file('P4','S','Migration completed (create jobs when you are done with testing.)') 
        else:
            logging.info('wrong choice given while creating jobs.')