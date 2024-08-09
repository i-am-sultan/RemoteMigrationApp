from google_sheet import *
from log_sheet import *

import socket
import os
import logging
import re
import psycopg2

patch_drill_path = r'C:\Program Files\edb\prodmig\PostMigPatches\patch_drill.sql'
patch_live_path = r'C:\Program Files\edb\prodmig\PostMigPatches\patch_live.sql'

# Logging Configuration
LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=LOG_FILE_PATH,filemode='a',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)

def updatePatchDrill(pgDbname, filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # Modify the content to replace dbname with pgDbname
        content = re.sub(r"OPTIONS \(dbname '[^']+\'", f"OPTIONS (dbname '{pgDbname}'", content)
        content = re.sub(r'REVOKE ALL ON DATABASE "[^"]+',f'REVOKE ALL ON DATABASE "{pgDbname}',content)
        content = re.sub(r'GRANT CONNECT ON DATABASE "[^"]+',f'GRANT CONNECT ON DATABASE "{pgDbname}',content)

        with open(filepath, 'w') as f:
            f.write(content)

        logging.info(f'Successfully updated patch_drill.sql for database {pgDbname}.')
        return 0
    except Exception as e:
        logging.info(f'\nError updating patch_drill.sql: {e}')
        return f'\nError updating patch_drill.sql: {e}'

def updatePatchLive(pgDbname, filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # Modify the content to replace dbname with pgDbname
        content = re.sub(r"OPTIONS \(dbname '[^']+\'", f"OPTIONS (dbname '{pgDbname}'", content)
        content = re.sub(r'REVOKE ALL ON DATABASE "[^"]+',f'REVOKE ALL ON DATABASE "{pgDbname}',content)
        content = re.sub(r'GRANT CONNECT ON DATABASE "[^"]+',f'GRANT CONNECT ON DATABASE "{pgDbname}',content)

        with open(filepath, 'w') as f:
            f.write(content)

        logging.info(f'Successfully updated patch_live.sql for database {pgDbname}.')
        return 0
    except Exception as e:
        logging.info(f'\nError updating patch_live.sql: {e}')
        return f'\nError updating patch_live.sql: {e}'

def executePatch(pgHost,pgPort,pgUserName,pgPass,pgDbname, patch_path):
    connection = None
    cursor = None
    try:
        # Read the SQL patch file
        with open(patch_path, 'r') as f1:
            content = f1.read()
        content = re.sub(r"dbname [^,]+", f"dbname '{pgDbname}'", content)
        with open(patch_path, 'w') as f1:
            f1.write(content)

        # Connect to the PostgreSQL database
        connection = psycopg2.connect(database=pgDbname, user=pgUserName, password=pgPass, host=pgHost, port=pgPort)
        cursor = connection.cursor()
        cursor.execute(content)
        connection.commit()

        # Log successful execution
        logging.info(f'Success: Executed patch {patch_path} on database {pgDbname}.')
        return 0
        
    except psycopg2.Error as e:
        # Log any psycopg2 database errors
        logging.info(f'\nError: Failed to execute patch {patch_path} on database {pgDbname}. Error: {e}')
        return f'\nError: Failed to execute patch {patch_path} on database {pgDbname}. Error: {e}'

    except Exception as e:
        # Log any other unexpected errors
        logging.info(f'\nError: Failed to execute patch {patch_path} on database {pgDbname}. Unexpected error: {e}')
        return f'\nError: Failed to execute patch {patch_path} on database {pgDbname}. Unexpected error: {e}'

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def execute_sql_patch(credentials, patch_choice):
    global patch_drill_path
    global patch_live_path
    try:
        if patch_choice == "drill":
            result = updatePatchDrill(credentials['pgDbName'], patch_drill_path)
            if result == 0:
                result = executePatch(credentials['pgHost'], credentials['pgPort'], credentials['pgUser'], credentials['pgPass'], credentials['pgDbName'], patch_drill_path)
                return result
            else:
                return result
        elif patch_choice == "live":
            result = updatePatchLive(credentials['pgDbName'], patch_live_path)
            if result == 0:
                result = executePatch(credentials['pgHost'], credentials['pgPort'], credentials['pgUser'], credentials['pgPass'], credentials['pgDbName'], patch_live_path)
                return result
            else:
                return result
    except Exception as e:
        print(f'Error executing SQL patch: {e}')
        return f"'{e}'"

if __name__ == "__main__":
    private_ip = get_private_ip()
    excel_df = access_sheet()
    credentials = load_credentials_from_excel(excel_df,private_ip)
    choice = input('Enter patch choice(live/drill): ')
    result = execute_sql_patch(credentials,'live')
    update_sheet(private_ip,'Status',result)