from concurrent.futures import ThreadPoolExecutor, as_completed
import psycopg2
import logging
import os
import socket
from google_sheet import *
from log_sheet import *
import status_update
import json

# Logging Configuration
LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=LOG_FILE_PATH, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def execute_procedure(connection_params, proc_call):
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**connection_params)
        connection.autocommit = True #default value is false
        cursor = connection.cursor()
        # Execute the procedure
        cursor.execute(proc_call)
        # connection.commit()  # Commit the transaction
        logging.info(f'Procedure call "{proc_call}" executed successfully.')
        return 0
    except psycopg2.Error as e:
        # Rollback the transaction if an error occurs
        connection.rollback()
        logging.error(f'Error: Failed to execute procedure call "{proc_call}". Error: {e}')
        return f'Error: Failed to execute procedure call "{proc_call}". Error: {e}'
    except Exception as e:
        logging.error(f'Unexpected error while executing procedure call "{proc_call}": {e}')
        return f'Unexpected error while executing procedure call "{proc_call}": {e}'
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def run_cube_population(credentials):
    
    pgHost = credentials['pgHost']
    pgPort = credentials['pgPort']
    pgUser = credentials['pgUser']
    pgPass = credentials['pgPass']
    pgDbname = credentials['pgDbName']
    
    connection_params = {
        'database': pgDbname,
        'user': pgUser,
        'password': pgPass,
        'host': pgHost,
        'port': pgPort
    }

    # List of procedure calls with parameters
    procedures = [
        "call main.db_pro_sitetositemovement_firsttimepopulation_outward('2023-04-01', CURRENT_DATE);",
        "call main.db_pro_sitetositemovement_firsttimepopulation_inward('2023-04-01', CURRENT_DATE);",
        "call main.db_pro_sitetositemovement_not_in_outward();",
        "call main.db_proc_sitetosite_intransum('2023-04-01');",
        "call main.db_pro_compositegst_firsttimepopulation('2023-04-01', CURRENT_DATE);",
        "call main.db_pro_stk_bk_summary_master_build('2023-04-01');",
        "call main.db_pro_stk_bk_batchwise_master_build('2023-04-01');",
        "call main.db_pro_stk_bk_summary_stockpointwise_master_build('2023-04-01');",
        "call main.db_pro_stk_bk_stockpointwise_batchwise_master_build('2023-04-01');",
        "call main.db_pro_stk_bk_costadj_master_build('2023-04-01');",
        "call main.db_pro_stk_bk_costadj_batchwise_master_build('2023-04-01');",
        "call main.db_pro_stk_ageing_firsttime();",
        "call main.db_pro_stk_ageing_stockpointwise_firsttime();"
    ]

    # Use ThreadPoolExecutor to run procedures concurrently
    results = []
    with ThreadPoolExecutor(max_workers=len(procedures)) as executor:
        future_to_proc = {executor.submit(execute_procedure, connection_params, proc): proc for proc in procedures}
        for future in as_completed(future_to_proc):
            proc = future_to_proc[future]
            try:
                # result = future.result()
                # results.append(str(result))
                results = 0
            except Exception as e:
                logging.error(f'Error while executing procedure: {e}')
                results.append(f'Error while executing procedure: {e}')
    
    # Combine all results
    if results:
        results = '\n'.join(results)
    return results

if __name__ == '__main__':
    current_user = os.getenv('USERNAME')
    status_file_path = f'C:\\Users\\{current_user}\\Desktop\\migration_status\\status.json'
    with open(status_file_path,'r') as status_file:
        status_content = json.load(status_file)
    if (status_content['Process'] == 'P5' and status_content['Status'] == 'O') or (status_content['Process'] == 'P5' and status_content['Status'] == 'F'):
        private_ip = get_private_ip()
        # excel_df = access_sheet()
        # credentials = load_credentials_from_excel(excel_df, private_ip)
        credentials = load_credentials_from_json(private_ip)
        cube_result = run_cube_population(credentials)
        if cube_result != 0:
            status_update.update_status_in_file('P5','F',f'Population of initial cube data failed. {cube_result}')
        else:
            status_update.update_status_in_file('P6','O','Initial cube data population started successfully. Barcode ctrl.exe executed...')       
        # update_sheet(private_ip, 'Status', f"'{result}'")
    else:
        logging.info('Process and Status is not matching to run run_cube_population.py')