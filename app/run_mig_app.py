from google_sheet import *
from log_sheet import *
import subprocess
import os
import psycopg2
import status_update
import json

migrationapp_path = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\RunEDBCommand.exe'

# Logging Configuration
LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=LOG_FILE_PATH,filemode='a',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)

def run_mig_app(app_path):
    command = app_path
    logging.info(f'migration app {app_path} started...')
    try:
        process = subprocess.run(
            command,
            capture_output = False, #When set to True, will capture the standard output and standard error.
            text=True, #When set to True, will return the stdout and stderr as string, otherwise as bytes.
            check = True #a boolean value that indicates whether to check the return code of the subprocess, if check is true and the return code is non-zero, then subprocess `CalledProcessError` is raised.
        )
        # logging.info(f'STDOUT: {process.stdout}')
        # logging.error(f'STDERR: {process.stderr}')

        if process.returncode == 0:
            logging.info(f'{app_path} executed successfully.')
            return 0
        else:
            logging.error(f'{app_path} failed with return code {process.returncode}.')
            return f'{app_path} failed with return code {process.returncode}.'

    except Exception as e:
        logging.error(f'Error running {app_path}: {e}')
        print(f'{e}')
        return str(e)

def check_run_mig_status(credentials):
    try:
        pgcon = psycopg2.connect(database=credentials['pgDbName'], user=credentials['pgUser'], password=credentials['pgPass'], host=credentials['pgHost'], port=credentials['pgPort'])
        cur = pgcon.cursor()
        cur.execute("SELECT * FROM oracle_data_count WHERE  UPPER(TABLE_NAME) <> 'ORACLE_DATA_COUNT' AND UPPER(TABLE_NAME) <> 'PSITE_EVENT_ARCHIVE' AND UPPER(TABLE_NAME) NOT LIKE 'GDS2_%' and UPPER(TABLE_NAME) NOT LIKE 'DX%' AND UPPER(TABLE_NAME) NOT LIKE '%NFS$%' AND UPPER(TABLE_NAME) NOT LIKE '%TEMP%' AND UPPER(TABLE_NAME) NOT LIKE '%STG%' AND UPPER(TABLE_NAME) NOT LIKE '%STAGING%' AND UPPER(TABLE_NAME) NOT LIKE '%INT$%' AND UPPER(TABLE_NAME) NOT LIKE '%SMS%' AND UPPER(TABLE_NAME) NOT LIKE '%AUD2%' AND UPPER(TABLE_NAME) NOT LIKE '%AUD%' AND UPPER(TABLE_NAME) NOT LIKE 'CUBE%' AND UPPER(TABLE_NAME) NOT LIKE '%BKP%' AND UPPER(TABLE_NAME) NOT LIKE '%_MV' AND UPPER(TABLE_NAME) NOT LIKE 'GLOBAL%' AND UPPER(TABLE_NAME) NOT LIKE 'MIS_CUBE$%' AND UPPER(TABLE_NAME) NOT LIKE 'MIS_MAS$%'  AND UPPER(TABLE_NAME) NOT LIKE 'MLOG$%' AND UPPER(TABLE_NAME) NOT LIKE 'MLOG$%' AND UPPER(TABLE_NAME) NOT IN (SELECT UPPER(viewname) AS view_name FROM pg_views WHERE schemaname = 'main') ORDER BY TABLE_NAME;")
        oracle_data = cur.fetchall()

        if not oracle_data:
            logging.info('No data found in table "oracle_data_count"')
            return 'No data found in table "oracle_data_count"'
        
        flag = 0        
        for tuples in oracle_data:
            table_name = tuples[0].lower()
            cur.execute(f'select count(*) from {table_name}')
            postgres_data_count = cur.fetchone()[0]
            print(f'{table_name}')
            print(credentials['pgDbName'])
            print(f'postgres_data_count: {postgres_data_count}')
            oracle_data_count = tuples[1]
            print(f'oracle_data_count: {oracle_data_count}')
            
            # print(f'oracle: {oracle_data_count},postgres: {postgres_data_count}')
            logging.info(f'{table_name}: Oracle: {oracle_data_count}, Postgres: {postgres_data_count}')
            
            if postgres_data_count != oracle_data_count:
                flag = 1
                logging.error(f'Row count mismatch for the table {table_name}: Oracle: {oracle_data_count}, Postgres: {postgres_data_count}')
            # else:
                # flag = 0
                #logging.info('No row count mismatch. Data Migration successfull.')
                #return 0
        if flag == 1:
            print('Data mismatch in tables')
            cur.close()
            pgcon.close()
            return f'Row count mismatch between Oracle and Postgres.'
        else:
            cur.close()
            pgcon.close()
            print('No data mismatch')
            logging.info('No row count mismatch. Data Migration successfull.')
            return 0


    except psycopg2.DatabaseError as e:
        logging.info(f'Error: Failed to connect to postgres database.\nError: {str(e)}')
        return f'{str(e)}'
    
if __name__ == '__main__':
    current_user = os.getenv('USERNAME')
    status_file_path = f'C:\\Users\\{current_user}\\Desktop\\migration_status\\status.json'
    with open(status_file_path,'r') as status_file:
        status_content = json.load(status_file)
    if (status_content['Process'] == 'P2' and status_content['Status'] == 'O') or (status_content['Process'] == 'P2' and status_content['Status'] == 'F'):
        try:
            private_ip = get_private_ip()
            print(private_ip)
            credentials = load_credentials_from_json(private_ip)
            check_run_mig_status = check_run_mig_status(credentials)
            print(check_run_mig_status)
            if check_run_mig_status != 0:
                status_update.update_status_in_file('P2','F', f'Migration failed! {check_run_mig_status}')
            else:
                status_update.update_status_in_file('P3','O','Data migration succeeded! (with no row count mismatch). Postmigration started...')
        except Exception as e:
            logging.error(f'An unexpected error occurred: {e}', exc_info=True)
    else:
        logging.info('Process and Status is not matching to run run_mig_app.py')