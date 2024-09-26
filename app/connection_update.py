from oauth2client.service_account import ServiceAccountCredentials
import socket
import pandas as pd
import logging
import os
import json
import shutil
from google_sheet import *
from log_sheet import *
import status_update



# Get current logged-in user
current_user = os.getenv('USERNAME')


# File Paths
ORACON_PATH = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\OraCon.txt'
PGCON_PATH = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\pgCon.txt'
SCHEMA_PATH = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\Config.json'
TOOLKIT_PATH = r'C:\Program Files\edb\mtk\etc\toolkit.properties'
CONNECTION_JSON_PATH = r'C:\Program Files\edb\prodmig\Ora2PGCompToolKit\Debug\Connection.json'
AUDIT_PATH = r'C:\Program Files\edb\prodmig\AuditTriggerCMDNew\netcoreapp3.1'
BARCODE_PATH = r'C:\Program Files\edb\prodmig\BarcodeFile\netcoreapp3.1'

# Logging Configuration
LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, f'migration_log_{socket.gethostname()}.log')

logging.basicConfig(
    filename=LOG_FILE_PATH,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def update_connections(credentials):
    try:
        # Update configuration files
        result = updateOraCon(credentials['oraSchema'], credentials['oraHost'], credentials['oraPort'], credentials['oraPass'], credentials['oraService'], ORACON_PATH)
        if result:
            return result
        updatepgCon(credentials['pgHost'], credentials['pgPort'], credentials['pgUser'], credentials['pgPass'], credentials['pgDbName'], PGCON_PATH)
        updateSchema(credentials['oraSchema'],SCHEMA_PATH)
        updateToolkit(credentials['oraSchema'], credentials['oraHost'], credentials['oraPort'], credentials['oraPass'], credentials['oraService'],
                      credentials['pgHost'], credentials['pgPort'], credentials['pgUser'], credentials['pgPass'], credentials['pgDbName'], TOOLKIT_PATH)
        updateConnectionJson(credentials['oraSchema'], credentials['oraHost'], credentials['oraPort'], credentials['oraPass'], credentials['oraService'],
                             credentials['pgHost'], credentials['pgPort'], credentials['pgUser'], credentials['pgPass'], credentials['pgDbName'], CONNECTION_JSON_PATH)

        # Copy the files to the destination directory
        if copyFiles(AUDIT_PATH) and copyFiles(BARCODE_PATH):
            logging.info('Connections updated and files copied successfully.')
            return 0
        else:
            logging.error('An error occurred while copying files.')
            return 'An error occurred while copying files.'
    except Exception as e:
        logging.error(f'An error occurred: {e}', exc_info=True)
        return str(e)

def updateOraCon(OraSchema, OraHost, OraPort, OraPass, OraService, filepath):
    content = (
        f"User Id={OraSchema};Password={OraPass};"
        f"Data Source=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={OraHost})(PORT={OraPort}))"
        f"(CONNECT_DATA=(SERVICE_NAME={OraService})))"
    )
    try:
        with open(filepath, 'w') as f1:
            f1.write(content)
        logging.info('OraCon updated successfully.')
        return 0
    except Exception as e:
        logging.error(f'Error updating OraCon.txt: {e}', exc_info=True)
        return f'{e}'

def updatepgCon(pgHost, pgPort, pgUser, pgPass, pgDbName, filepath):
    content = (f"Server={pgHost};Port={pgPort};Database={pgDbName};User Id={pgUser};Password={pgPass};ApplicationName=w3wp.exe;Ssl Mode=Require;")
    # content = (f"Server={pgHost};Port={pgPort};Database={pgDbName};User Id={pgUser};Password={pgPass};ApplicationName=w3wp.exe;Ssl Mode=Require;")
    try:
        with open(filepath, 'w') as f1:
            f1.write(content)
        logging.info('pgCon updated successfully.')
    except Exception as e:
        logging.error(f'Error updating pgCon.txt: {e}', exc_info=True)
        
def updateSchema(oraSchema,filepath):
    try:
        with open(filepath, 'r') as f:
            content = json.load(f)
            content["SCHEMA_NAME"] = f'{oraSchema}'
        with open(filepath,'w') as f:
            json.dump(content,f,indent=4)

        logging.info('config.json successfully updated.')
    except FileNotFoundError:
        logging.error(f'Error: File {filepath} not found.')
    except json.JSONDecodeError as e:
        logging.error(f'Error decoding JSON from {filepath}: {e}', exc_info=True)
    except Exception as e:
        logging.error(f'Error updating config.json: {e}', exc_info=True)

def updateToolkit(OraSchema, OraHost, OraPort, OraPass, OraService, pgHost, pgPort, pgUser, pgPass, pgDbName, filepath):
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
        logging.info('toolkit.properties updated successfully.')
    except FileNotFoundError:
        logging.error(f'Error: file {filepath} not found.')
    except Exception as e:
        logging.error(f'Error updating toolkit.properties: {e}', exc_info=True)

def updateConnectionJson(OraSchema, OraHost, OraPort, OraPass, OraService, pgHost, pgPort, pgUser, pgPass, pgDbName, filepath):
    try:
        with open(filepath, 'r') as f:
            connections = json.load(f)
        connections["Connection_1"] = f"Data Source=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={OraHost})(PORT={OraPort}))(CONNECT_DATA=(SERVICE_NAME={OraService})));User Id={OraSchema};Password={OraPass};DatabaseType=ORACLE"
        connections["Connection_2"] = f"Server={pgHost};Port={pgPort};Database={pgDbName};User Id={pgUser};Password={pgPass};ApplicationName=w3wp.exe;Ssl Mode=Require;DatabaseType=POSTGRES"
        with open(filepath, 'w') as f:
            json.dump(connections, f, indent=4)
        logging.info('connection.json updated successfully.')
    except FileNotFoundError:
        logging.error(f'Error: File {filepath} not found.')
    except json.JSONDecodeError as e:
        logging.error(f'Error decoding JSON from {filepath}: {e}', exc_info=True)
    except Exception as e:
        logging.error(f'Error updating connection.json: {e}', exc_info=True)

def copyFiles(destination_dir):
    try:
        shutil.copy(ORACON_PATH, destination_dir)
        shutil.copy(PGCON_PATH, destination_dir)
        logging.info('OraCon.txt and pgCon.txt copied successfully.')
        return True
    except Exception as e:
        logging.error(f'Error copying files: {e}', exc_info=True)
        return False

if __name__ == "__main__":
    
    status_file_path = f'C:\\Users\\{current_user}\\Desktop\\migration_status\\status.json'
    print(status_file_path)

    with open(status_file_path,'r') as status_file:
        status_content = json.load(status_file)
    if status_content['Process'] == 'P1' and status_content['Status'] == 'O':
        try:
            private_ip = get_private_ip()
            credentials = load_credentials_from_json(private_ip)

            cred_update_result = update_connections(credentials)
            if cred_update_result:
                status_update.update_status_in_file('P1','F',f'{cred_update_result}')
            else:
                status_update.update_status_in_file('P2','O','Credentials updated successfully. EDB toolkit started...')
                logging.info('Credentials updated successfully. EDB toolkit started...')
        except Exception as e:
            logging.error(f'An unexpected error occurred: {e}', exc_info=True)
    else :
        logging.info('Process and Status is not matching to run connection_update.py')