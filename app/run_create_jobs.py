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
    
    print(pgDbname);

    connection = None
    cursor = None
    try:
        # Connect to the PostgreSQL database and execute the job creation procedure.
        connection = psycopg2.connect(database=pgDbname, user=pgUserName, password=pgPass, host=pgHost, port=pgPort)
        cursor = connection.cursor()
        cursor.execute('call main.schedule_jobs_in_postgres()')
        connection.commit()
        logging.info(f'Successfully created jobs for the database {pgDbname}.')
        return 0
    except psycopg2.Error as e:
        logging.info(f'Error creating jobs for the database {pgDbname}: {e}')
        return f'Error creating jobs for the database {pgDbname}: {e}'
    except Exception as e:
        logging.info(f'Unexpected error while creating jobs for the database {pgDbname}: {e}')
        return f'Unexpected error while creating jobs for the database {pgDbname}: {e}'
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
    if (status_content['Process'] == 'P7' and status_content['Status'] == 'O') or (status_content['Process'] == 'P7' and status_content['Status'] == 'F'):
        private_ip = get_private_ip()
        # excel_df = access_sheet()
        # credentials = load_credentials_from_excel(excel_df,private_ip)
        credentials = load_credentials_from_json(private_ip)
        try:
            if sys.argv[1] == 'drill' or 'live':
                jobs_result = create_database_jobs(credentials)
                print(jobs_result)
                if jobs_result:
                    status_update.update_status_in_file('P7','F',f'Error while creating jobs {jobs_result}')
                else:
                    status_update.update_status_in_file('P8','O','Database jobs created.(Report migration started...)')   
            # elif sys.argv[1] == 'live':
            #     # print(jobs_result)
            #     if (status_content['Process'] == 'P6' and status_content['Status'] == 'O'):
            #         status_update.update_status_in_file('P6','F','Migration completed! (create jobs only when you are done with testing.)') 
            #     if (status_content['Process'] == 'P6' and status_content['Status'] == 'F'):
            #         jobs_result = create_database_jobs(credentials)
            #         if jobs_result:
            #             status_update.update_status_in_file('P6','F',f'Error while creating jobs {jobs_result}')
            #         else:
            #             status_update.update_status_in_file('P6','S','Migration completed (Database jobs created.)')  
            else:
                logging.info('wrong choice given while creating jobs.')
        except Exception as e:
            logging.error(f'An unexpected error occurred: {e}')
    else:
        logging.info('Process and Status is not matching to run run_create_jobs.py')