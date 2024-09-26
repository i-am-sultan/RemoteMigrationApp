import os
import cx_Oracle
import psycopg2
import socket
import logging
import pandas as pd
from google_sheet import *
from log_sheet import *
import status_update
import json

log_dir = os.getcwd()
log_file_path = os.path.join(log_dir,'logs',f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=log_file_path,filemode='a',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)

def compare_versions(credentials):
    try:
        oracon = cx_Oracle.connect(f'{credentials['oraSchema']}/{credentials['oraPass']}@{credentials['oraHost']}:{credentials['oraPort']}/{credentials['oraService']}')
        cur = oracon.cursor()
        cur.execute('select db_version from gateway.packdef')
        ora_version = cur.fetchone()[0]
        cur.close()
        oracon.close()
    except cx_Oracle.DatabaseError as e:
        logging.info(f'Error: Failed to connect to Oracle database.\nError: {str(e)}')
        return {str(e)}
    try:
        pgcon = psycopg2.connect(database=credentials['pgDbName'], user=credentials['pgUser'], password=credentials['pgPass'], host=credentials['pgHost'], port=credentials['pgPort'])
        cur = pgcon.cursor()
        cur.execute('select db_version from gateway.packdef')
        pg_version = cur.fetchone()[0]
        cur.close()
        pgcon.close()
    except psycopg2.DatabaseError as e:
        logging.info(f'Error: Failed to connect to postgres database.\nError: {str(e)}')
        return {str(e)}
    
    if ora_version == pg_version:
        msg = f'Success: Great, Version Matched!\nOracle({ora_version}) and Postgres({pg_version}) Version are the same,now you can proceed with migration!'
        logging.info(msg)
        return 0
    else:
        msg = f'Error: Version Mismatch!\nOracle Version : {ora_version} and PostgreSQL Version: {pg_version}'
        logging.info(msg)
        return msg

if __name__ == "__main__":
    current_user = os.getenv('USERNAME')
    # status_file_path = r'C:\Users\ginesysdevops\Desktop\migration_status\status.json'
    status_file_path = f'C:\\Users\\{current_user}\\Desktop\\migration_status\\status.json'
    with open(status_file_path,'r') as status_file:
        status_content = json.load(status_file)
        
    if status_content['Process'] == 'P1' and status_content['Status'] == 'O':
        private_ip = get_private_ip()
        credentials = load_credentials_from_json(private_ip)
        version_check_result = compare_versions(credentials)
        if version_check_result !=0:
            status_update.update_status_in_file('P1','F',f'{version_check_result}')
        else:
            status_update.update_status_in_file('P1','O','DBVersion Matched')
    else:
        logging.info('Process and Status is not matching to run ora_pg_version_check.py')