import gspread
from oauth2client.service_account import ServiceAccountCredentials
import cx_Oracle
import os
import psycopg2
import socket
import logging
import pandas as pd
from sheet import *

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
        return msg
    else:
        msg = f'Error: Version Mismatch!\nOracle Version : {ora_version} and PostgreSQL Version: {pg_version}'
        logging.info(msg)
        return msg

if __name__ == "__main__":
    private_ip = get_private_ip()
    excel_df = access_sheet()
    credentials = load_credentials_from_excel(excel_df,private_ip)
    result = compare_versions(credentials)
    if result:
        update_sheet(private_ip)
        logging.info('Status updated in google sheet.')
    else:
        logging.info('Credentials not updated, check error log.')