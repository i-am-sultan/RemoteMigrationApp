import os
import psycopg2
import socket
import logging
import pandas as pd
import subprocess
from sheet import *

comparetoolapp_path = r'C:\Program Files\edb\prodmig\Ora2PGCompToolKit\Debug\OraPostGreSqlComp.exe'

log_dir = os.getcwd() 
log_file_path = os.path.join(log_dir,'logs',f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=log_file_path,filemode='a',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)

def run_compare_tool(app_path):
    try:
        process = subprocess.Popen(
            app_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Wait for the process to complete and get the output and error
        stdout, stderr = process.communicate()
        
        if stdout:
            logging.info(f'Stdout from {app_path}:')
            logging.info(stdout)
            if stderr:
                logging.error(f'Stderr from {app_path}:')
                logging.error(stderr)
                return stderr + stdout
        else:
            logging.info(f'{app_path} executed successfully.')
            return f'{app_path} executed successfully.'

    except Exception as e:
        logging.error(f'Error running {app_path}: {e}')
        return e
'''
def row_count_compare(credentials):
    try:
        pgcon = psycopg2.connect(database=credentials['pgDbName'], user=credentials['pgUser'], password=credentials['pgPass'], host=credentials['pgHost'], port=credentials['pgPort'])
        cur = pgcon.cursor()
        cur.execute('select * from oracle_data_count order by table_name limit 10')
        oracle_data = cur.fetchall()
        for tuples in oracle_data:
            table_name = tuples[0].lower()
            cur.execute(f'select count(*) from {table_name}')
            postgres_data_count = cur.fetchone()[0]
            oracle_data_count = tuples[1]

            if postgres_data_count != oracle_data_count:
                logging.warning(f'Oracle and Postgres row count mismatch.\nOracle: {oracle_data_count}\nPostgres: {postgres_data_count}')
                return f'Oracle and Postgres row count mismatch.\nOracle: {oracle_data_count}\nPostgres: {postgres_data_count}'
            else:
                return f'Data Validation Done(No mismatch in row count).'
        cur.close()
        pgcon.close()
    except psycopg2.DatabaseError as e:
        logging.info(f'Error: Failed to connect to postgres database.\nError: {str(e)}')
        return {str(e)}
    '''
if __name__ == "__main__":
    private_ip = get_private_ip()
    result = run_compare_tool(comparetoolapp_path)
    print(result)
    update_sheet(private_ip,'Status',f"'{result}'")