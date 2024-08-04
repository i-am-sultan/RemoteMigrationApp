import sys
import re
import json
import shutil
import subprocess
import psycopg2
import os
import pandas as pd
import logging
import time
import socket

oracon_path = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\OraCon.txt'
pgcon_path = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\pgCon.txt'
toolkit_path = r'C:\Program Files\edb\mtk\etc\toolkit.properties'
connection_json_path = r'C:\Program Files\edb\prodmig\Ora2PGCompToolKit\Debug\Connection.json'
audit_path = r'C:\Program Files\edb\prodmig\AuditTriggerCMDNew\netcoreapp3.1'
patch_drill_path = r'C:\Program Files\edb\prodmig\PostMigPatches\patch_drill.sql'
patch_live_path = r'C:\Program Files\edb\prodmig\PostMigPatches\patch_live.sql'
job_patch_path = r'C:\Program Files\edb\prodmig\PostMigPatches\patch_jobs.sql'
migrationapp_path = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\RunEDBCommand.exe'
audittriggerapp_path = r'C:\Program Files\edb\prodmig\AuditTriggerCMDNew\netcoreapp3.1\TriggerConstraintViewCreationForAuditPostMigration.exe'
comparetoolapp_path = r'C:\Program Files\edb\prodmig\Ora2PGCompToolKit\Debug\OraPostGreSqlComp.exe'

log_dir = r'C:\Users\ginesysdevops\Desktop\Remote'
log_file_path = os.path.join(log_dir, f'migration_log_{socket.gethostname()}.log')
with open(log_file_path,'w') as logfile:
    logfile.write('\n')
logging.basicConfig(filename=log_file_path,filemode='a',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)
            
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
        # Pre-specified file paths
        global oracon_path
        global pgcon_path

        shutil.copy(oracon_path, destination_dir)
        shutil.copy(pgcon_path, destination_dir)
        
        logging.info(f'OraCon.txt and pgCon.txt copied and pasted successfully...')
        return True
    except Exception as e:
        logging.info(f'\nError copying files: {e}')
        return False

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
    except Exception as e:
        logging.info(f'\nError updating patch_drill.sql: {e}')

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
    except Exception as e:
        logging.info(f'\nError updating patch_live.sql: {e}')


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
        
        connection = psycopg2.connect(database=pgDbname, user=pgUserName, password=pgPass, host=pgHost, port=pgPort)
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute('CALL populate_first_time_migdata()')
        # Commit the transaction
        connection.commit()
        # Log successful execution
        logging.info(f'Success: Executed patch {patch_path} on database {pgDbname}.')
    except psycopg2.Error as e:
        # Log any psycopg2 database errors
        logging.info(f'\nError: Failed to execute patch {patch_path} on database {pgDbname}. Error: {e}')
    except Exception as e:
        # Log any other unexpected errors
        logging.info(f'\nError: Failed to execute patch {patch_path} on database {pgDbname}. Unexpected error: {e}')
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
def createJobs(schema_name, pgHost, pgPort, pgUserName, pgPass, pgDbname, job_patch_path):
    connection = None
    cursor = None
    
    try:
        with open(job_patch_path, 'r') as f1:
            content = f1.read()

        patterns = [
            (r"select cron\.schedule_in_database\('GINESYS_AUTO_SETTLEMENT_JOB_[^']+','[^']+','[^']+','[^']+'\);",
             f"select cron.schedule_in_database('GINESYS_AUTO_SETTLEMENT_JOB_{schema_name.upper()}','*/15 * * * *','call main.db_pro_auto_settle_unpost()','{pgDbname}');"),
            (r"select cron\.schedule_in_database\('GINESYS_DATA_SERVICE_2[^']+','[^']+','[^']+','[^']+'\);",
             f"select cron.schedule_in_database('GINESYS_DATA_SERVICE_2_{schema_name.upper()}','*/1 * * * *','call main.db_pro_gds2_event_enqueue()','{pgDbname}');"),
            (r"select cron\.schedule_in_database\('GINESYS_INVSTOCK_INTRA_LOG_AGG[^']+','[^']+','[^']+','[^']+'\);",
             f"select cron.schedule_in_database('GINESYS_INVSTOCK_INTRA_LOG_AGG_{schema_name.upper()}','30 seconds','call main.invstock_intra_log_refresh()','{pgDbname}');"),
            (r"select cron\.schedule_in_database\('GINESYS_INVSTOCK_LOG_AGG[^']+','[^']+','[^']+','[^']+'\);",
             f"select cron.schedule_in_database('GINESYS_INVSTOCK_LOG_AGG_{schema_name.upper()}','30 seconds','call main.invstock_log_refresh()','{pgDbname}');"),
            (r"select cron\.schedule_in_database\('GINESYS_PERIOD_CLOSURE_JOB[^']+','[^']+','[^']+','[^']+'\);",
             f"select cron.schedule_in_database('GINESYS_PERIOD_CLOSURE_JOB_{schema_name.upper()}','*/2 * * * *','call main.db_pro_period_closure_dequeue()','{pgDbname}');"),
            (r"select cron\.schedule_in_database\('GINESYS_POS_STLM_AUDIT[^']+','[^']+','[^']+','[^']+'\);",
             f"select cron.schedule_in_database('GINESYS_POS_STLM_AUDIT_{schema_name.upper()}','*/5 * * * *','call main.db_pro_pos_stlm_audit()','{pgDbname}');"),
            (r"select cron\.schedule_in_database\('GINESYS_RECALCULATE_TAX_JOB[^']+','[^']+','[^']+','[^']+'\);",
             f"select cron.schedule_in_database('GINESYS_RECALCULATE_TAX_JOB_{schema_name.upper()}','*/30 * * * *','call main.db_pro_recalculategst()','{pgDbname}');"),
            (r"select cron\.schedule_in_database\('GINESYS_STOCK_BOOK_PIPELINE_DELTA_AGG[^']+','[^']+','[^']+','[^']+'\);",
             f"select cron.schedule_in_database('GINESYS_STOCK_BOOK_PIPELINE_DELTA_AGG_{schema_name.upper()}','*/5 * * * *','call db_pro_delta_agg_pipeline_stock()','{pgDbname}');"),
            (r"select cron\.schedule_in_database\('GINESYS_STOCK_BOOK_SUMMARY_DELTA_AGG[^']+','[^']+','[^']+','[^']+'\);",
             f"select cron.schedule_in_database('GINESYS_STOCK_BOOK_SUMMARY_DELTA_AGG_{schema_name.upper()}','*/5 * * * *','call db_pro_delta_agg_stock_book_summary()','{pgDbname}');"),
            (r"select cron\.schedule_in_database\('GINESYS_STOCK_AGEING_DELTA_AGG[^']+','[^']+','[^']+','[^']+'\);",
             f"select cron.schedule_in_database('GINESYS_STOCK_AGEING_DELTA_AGG_{schema_name.upper()}','*/5 * * * *','call db_pro_delta_agg_stock_age_analysis()','{pgDbname}');")
        ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        with open(job_patch_path, 'w') as f1:
            f1.write(content)

        # Connect to the PostgreSQL database and execute the patched SQL
        connection = psycopg2.connect(database='postgres', user=pgUserName, password=pgPass, host=pgHost, port=pgPort)
        cursor = connection.cursor()
        cursor.execute(content)
        connection.commit()

        logging.info(f'Successfully executed job patch {job_patch_path} on database {pgDbname}.')
    except psycopg2.Error as e:
        logging.info(f'\nError executing job patch {job_patch_path} on database {pgDbname}: {e}')
    except Exception as e:
        logging.info(f'\nUnexpected error executing job patch {job_patch_path} on database {pgDbname}: {e}')
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def load_credentials_from_excel(excel_filepath,remotehost):
    credentials = {}
    try:
        df = pd.read_excel(excel_filepath)
        row = df[df['Hostname'] == remotehost]
        if not row.empty:
            # Extract Oracle credentials
            credentials['oraSchema'] = row['OraSchema'].values[0]
            credentials['oraHost'] = row['OraHost'].values[0]
            credentials['oraPort'] = row['OraPort'].values[0]
            credentials['oraPass'] = row['OraPass'].values[0]
            credentials['oraService'] = row['OraService'].values[0]

            # Extract PostgreSQL credentials
            credentials['pgDbName'] = row['PgDBName'].values[0]
            credentials['pgHost'] = row['PgHost'].values[0]
            credentials['pgPort'] = row['PgPort'].values[0]
            credentials['pgPass'] = row['PgPass'].values[0]
            credentials['pgUser'] = row['PgUser'].values[0]
            logging.info(f"Credentials successfully loaded from file {excel_filepath} \n{credentials}")
        else:
            logging.info(f"\nError: No entry found for the remote host {remotehost}")
    except Exception as e:
        logging.info(f'\nError loading credentials from the excel file: {e}')
    return credentials

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
        else:
            logging.info('An error occurred while copying files.')
    except Exception as e:
        logging.info(f'An error occurred: {e}')

def execute_sql_patch(credentials, patch_choice):
    try:
        if patch_choice == "Drill":
            updatePatchDrill(credentials['pgDbName'], patch_drill_path)
            executePatch(credentials['pgHost'], credentials['pgPort'], credentials['pgUser'], credentials['pgPass'], credentials['pgDbName'], patch_drill_path)
        elif patch_choice == "Live Migration":
            updatePatchLive(credentials['pgDbName'], patch_live_path)
            executePatch(credentials['pgHost'], credentials['pgPort'], credentials['pgUser'], credentials['pgPass'], credentials['pgDbName'], patch_live_path)
    except Exception as e:
        print(f'Error executing SQL patch: {e}')

def create_jobs(credentials):
    try:
        createJobs(credentials['oraSchema'], credentials['pgHost'], credentials['pgUser'], credentials['pgPort'], credentials['pgPass'], credentials['pgDbName'], job_patch_path)
    except Exception as e:
        print(f'Error creating jobs: {e}')

def run_external_app(app_path, inputs=None):
    try:
        if sys.platform.startswith('win'):
            logging.info('Lucky you! You are using Windows!')
            process = subprocess.Popen(
                app_path,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True  # This will automatically handle the encoding/decoding
            )

            if inputs:
                for input_data in inputs:
                    time.sleep(input_data.get('delay', 0))  # Wait for a specific period before sending the input
                    process.stdin.write(f"{input_data['value']}\n")
                    process.stdin.flush()

            stdout, stderr = process.communicate()

            if stdout:
                logging.info(f'Stdout from {app_path}:')
                logging.info(stdout)
            if stderr:
                logging.error(f'Stderr from {app_path}:')
                logging.error(stderr)
            else:
                logging.info(f'{app_path} executed successfully.')

            return process.returncode
        else:
            logging.info('Unsupported OS.')
            return
    except Exception as e:
        logging.error(f'Error running {app_path}: {e}')
        return -1



# Entry point for the application
if __name__ == '__main__':
    excel_filepath = r'C:\Users\ginesysdevops\Desktop\Remote\PG Automation.xlsx'
    hostname_filepath = r'C:\Users\ginesysdevops\Desktop\Remote\current_host.txt'
    with open(hostname_filepath,'r') as f1:
        current_hostname=f1.read()
    credentials = load_credentials_from_excel(excel_filepath,current_hostname)
    update_connections(credentials)
    oracle_schema_name = credentials['oraSchema']
    app_paths = [
        (migrationapp_path, [
            {'value': '1', 'delay': 0},  # First input immediately
            {'value': f'{oracle_schema_name}', 'delay': 20}  # Second input after 2 minutes
        ]),
        (audittriggerapp_path, None)  # No input needed for the second app
    ]    
    for app,inputs in app_paths:
        return_code = run_external_app(app,inputs)
        if return_code != 0:
            logging.error(f'{app} exited with code {return_code}. Stopping execution.')
            break
    # if return_code = 0:
        # updatePatchDrill(credentials['pgDbName'],patch_drill_path)
        # # updatePatchLive(credentials['pgDbName'],patch_live_path)
        # executePatch(
        #     credentials['pgHost'],
        #     credentials['pgPort'],
        #     credentials['pgUser'],
        #     credentials['pgPass'],
        #     credentials['pgDbName'],
        #     patch_drill_path)

        # createJobs(
        #     credentials['oraSchema'],
        #     credentials['pgHost'],
        #     credentials['pgPort'],
        #     credentials['pgUser'],
        #     credentials['pgPass'],
        #     credentials['pgDbName'],
        #     patch_drill_path)