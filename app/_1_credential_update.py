import gspread
from oauth2client.service_account import ServiceAccountCredentials
import socket
import pandas as pd
import logging
import os
import json
import shutil
from sheet import *

oracon_path = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\OraCon.txt'
pgcon_path = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\pgCon.txt'
toolkit_path = r'C:\Program Files\edb\mtk\etc\toolkit.properties'
connection_json_path = r'C:\Program Files\edb\prodmig\Ora2PGCompToolKit\Debug\Connection.json'
audit_path = r'C:\Program Files\edb\prodmig\AuditTriggerCMDNew\netcoreapp3.1'


log_dir = os.getcwd()
log_file_path = os.path.join(log_dir,'logs',f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=log_file_path,filemode='a',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)


def update_connections(credentials):
    try:
        # Pre-specified file paths
        updateOraCon(credentials['oraSchema'], credentials['oraHost'], credentials['oraPort'], credentials['oraPass'], credentials['oraService'], oracon_path)
        updatepgCon(credentials['pgHost'], credentials['pgPort'], credentials['pgUser'], credentials['pgPass'], credentials['pgDbName'], pgcon_path)
        updateToolkit(credentials['oraSchema'], credentials['oraHost'], credentials['oraPort'], credentials['oraPass'], credentials['oraService'],
                      credentials['pgHost'], credentials['pgPort'], credentials['pgUser'], credentials['pgPass'], credentials['pgDbName'], toolkit_path)
        updateConnectionJson(credentials['oraSchema'], credentials['oraHost'], credentials['oraPort'], credentials['oraPass'], credentials['oraService'],
                             credentials['pgHost'], credentials['pgPort'], credentials['pgUser'], credentials['pgPass'], credentials['pgDbName'], connection_json_path)

        # Copy the files to the destination directory
        success = copyFiles(audit_path)
        if success:
            logging.info('Connections updated and files copied successfully.')
            return 1
        else:
            logging.info('An error occurred while copying files.')
            return 0
    except Exception as e:
        logging.info(f'An error occurred: {e}')
        return f'{e}'

def updateOraCon(OraSchema, OraHost, oraPort, OraPass, OraService, filepath):
    content = (
            f"User Id={OraSchema};Password={OraPass};"
            f"Data Source=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={OraHost})(PORT={oraPort}))"
            f"(CONNECT_DATA=(SERVICE_NAME={OraService})))"
        )
    with open(filepath, 'w') as f1:
        f1.write(content)
    logging.info('OraCon updated successfully...')

def updatepgCon(pgHost, pgPort, pgUser, pgPass, pgDbName, filepath):
    content = (f"Server={pgHost};Port={pgPort};Database={pgDbName};User Id={pgUser};Password={pgPass};ApplicationName=w3wp.exe;Ssl Mode=Require;")
    with open(filepath, 'w') as f1:
        f1.write(content)
    logging.info('pgCon updated successfully... ')

def updateToolkit(OraSchema, OraHost, OraPort, OraPass, OraService, pgHost, pgPort, pgUser, pgPass, pgDbName, filepath):
    # Prepare the new properties
    oracle_url = f"jdbc:oracle:thin:@{OraHost}:{OraPort}:{OraService}"
    postgres_url = f"jdbc:postgresql://{pgHost}:{pgPort}/{pgDbName}"
    
    content = (
        f"SRC_DB_URL={oracle_url}\n"
        f"SRC_DB_USER={OraSchema}\n"
        f"SRC_DB_PASSWORD={OraPass}\n\n"
        f"TARGET_DB_URL={postgres_url}\n"
        f"TARGET_DB_USER={pgUser}\n"
        f"TARGET_DB_PASSWORD={pgPass}\n"
    )   
    try: 
        with open(filepath, 'w') as f1:
            f1.write(content)
    except FileNotFoundError:
        logging.info(f'\nError: file {filepath} not found.')
    except Exception as e:
        logging.info(f'\nError: updating file toolkit.properties: {str(e)}')
    logging.info('toolkit.properties updated successfully...')

def updateConnectionJson(OraSchema, OraHost, OraPort, OraPass, OraService, pgHost, pgPort, pgUser, pgPass, pgDbName, filepath):
    try:
        with open(filepath, 'r') as f:
            connections = json.load(f)
        # Update the Oracle connection string
        connections["Connection_1"] = f"Data Source=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={OraHost})(PORT={OraPort}))(CONNECT_DATA=(SERVICE_NAME={OraService})));User Id={OraSchema};Password={OraPass};DatabaseType=ORACLE"
        # Update the PostgreSQL connection string
        connections["Connection_2"] = f"Server={pgHost};Port={pgPort};Database={pgDbName};User Id={pgUser};Password={pgPass};ApplicationName=w3wp.exe;Ssl Mode=Require;DatabaseType=POSTGRES"
        with open(filepath, 'w') as f:
            json.dump(connections, f, indent=4)
        logging.info('connection.json updated successfully...')
    except FileNotFoundError:
        logging.info(f'\nError: File {filepath} not found.')
    except json.JSONDecodeError as e:
        logging.info(f'\nError: Failed to decode JSON from {filepath}. Details: {str(e)}')
    except Exception as e:
        logging.info(f'\nError updating connection.json: {str(e)}')
def copyFiles(destination_dir):
    try:
        shutil.copy(oracon_path, destination_dir)
        shutil.copy(pgcon_path, destination_dir)
        
        logging.info(f'OraCon.txt and pgCon.txt copied and pasted successfully...')
        return True
    except Exception as e:
        logging.info(f'\nError copying files: {e}')
        return False

if __name__ == "__main__":
    private_ip = get_private_ip()
    excel_df = access_sheet()
    # print(socket.gethostname())
    credentials = load_credentials_from_excel(excel_df,private_ip)
    result = update_connections(credentials)
    if result:
        update_sheet(private_ip)
        logging.info('Status updated in google sheet.')
    else:
        logging.info('Credentials not updated, check error log.')
