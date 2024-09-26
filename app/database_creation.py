import psycopg2
import logging
import os
import socket
import google_sheet as gsheet
import status_update
import json
import pandas

# Logging Configuration
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=log_file_path, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def check_if_exists_samedb(credentials):
    """Check if the target database already exists."""
    pgHost = credentials['pgHost']
    pgPort = credentials['pgPort']
    pgUserName = credentials['pgUser']
    pgPass = credentials['pgPass']
    pgDbname = credentials['pgDbName']

    query = 'SELECT 1 FROM pg_database WHERE datname = %s;'
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(database='postgres', user=pgUserName, password=pgPass, host=pgHost, port=pgPort)
        cursor = connection.cursor()
        cursor.execute(query, (pgDbname,))
        result = cursor.fetchone()
        if result:
            logging.info(f'Database "{pgDbname}" already exists.')
            return True
        else:
            logging.info(f'Database "{pgDbname}" does not exist.')
            return False
    except psycopg2.DatabaseError as db_err:
        logging.error(f'Error checking database existence: {db_err}')
        return None
    except Exception as e:
        logging.error(f'Unexpected error during check_if_exists_samedb: {e}')
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def terminate_connections(credentials, source_db):
    """Terminate all connections to a specific database."""
    pgHost = credentials['pgHost']
    pgPort = credentials['pgPort']
    pgUserName = credentials['pgUser']
    pgPass = credentials['pgPass']
    pgDbname = credentials['pgDbName']

    query = f'''
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = %s AND pid <> pg_backend_pid();
    '''
    
    connection = None
    cursor = None
    
    try:
        connection = psycopg2.connect(database='postgres', user=pgUserName, password=pgPass, host=pgHost, port=pgPort)
        cursor = connection.cursor()
        cursor.execute(query, (source_db,))
        connection.commit()
        logging.info(f'All connections to database "{source_db}" have been terminated.')
        return 0
    except psycopg2.DatabaseError as db_err:
        logging.error(f'Database error while terminating connections: {db_err}')
        return f'Error terminating connections: {db_err}'
    except Exception as e:
        logging.error(f'Unexpected error terminating connections: {e}')
        return f'Error terminating connections: {e}'
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_database(migration_type, credentials, source_db):
    """Create the target database and handle the migration logic based on migration type."""
    pgHost = credentials['pgHost']
    pgPort = credentials['pgPort']
    pgUserName = credentials['pgUser']
    pgPass = credentials['pgPass']
    pgDbname = credentials['pgDbName']

    if check_if_exists_samedb(credentials):
        terminate_connections_result = terminate_connections(credentials, pgDbname)
        if terminate_connections_result:
            return terminate_connections_result

        logging.info('Database already exists. Trying to drop the existing database...')
        db_drop_content = f'DROP DATABASE IF EXISTS "{pgDbname}";'
        unschedule_job_content = f'''   
            DO $$
            DECLARE
                i INT;
            BEGIN
                FOR i IN (SELECT jobid FROM cron.job WHERE database = '{pgDbname}')
                LOOP
                    EXECUTE FORMAT('SELECT cron.unschedule(%s)', i);
                END LOOP;
            END $$;
        '''
        
        connection = None
        cursor = None
        try:
            connection = psycopg2.connect(database='postgres', user=pgUserName, password=pgPass, host=pgHost, port=pgPort)
            connection.autocommit = True
            cursor = connection.cursor()
            
            if migration_type.lower() == 'drill':
                cursor.execute(unschedule_job_content)
                cursor.execute(db_drop_content)
                logging.info(f'Database "{pgDbname}" successfully dropped.')
            elif migration_type.lower() == 'live':
                cursor.execute(unschedule_job_content)
                logging.info(f'Unscheduled jobs for the database "{pgDbname}".')
                logging.warning(f'Cannot drop the database during Live Migration. Manual intervention needed.')
                return f'Cannot drop the database during Live Migration. Please drop manually if necessary.'
            else:
                logging.error(f'Invalid migration type specified: "{migration_type}".')
                return f'Invalid migration type "{migration_type}".'
        except psycopg2.DatabaseError as db_err:
            logging.error(f'Error dropping the database: {db_err}')
            return f'Error dropping the database: {db_err}'
        except Exception as e:
            logging.error(f'Unexpected error while dropping the database: {e}')
            return f'Error dropping the database: {e}'
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    # Proceed to create the new database
    terminate_connections(credentials, source_db)
    
    create_db_query = f'''CREATE DATABASE "{pgDbname}"
                          WITH OWNER = {pgUserName}
                          ENCODING = 'UTF8'
                          LC_COLLATE = 'C'
                          LC_CTYPE = 'C'
                          LOCALE_PROVIDER = 'libc'
                          CONNECTION LIMIT = -1
                          TEMPLATE = {source_db};'''

    alter_db_query = f'''
        ALTER DATABASE "{pgDbname}" SET search_path TO main, public, gateway, ginview, ginarchive;
        ALTER DATABASE "{pgDbname}" SET "TimeZone" TO 'Asia/Kolkata';
    '''

    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(database='postgres', user=pgUserName, password=pgPass, host=pgHost, port=pgPort)
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute(create_db_query)
        cursor.execute(alter_db_query)
        logging.info(f'Database "{pgDbname}" created successfully.')
        return 0
    except psycopg2.DatabaseError as db_err:
        logging.error(f'Error creating the database: {db_err}')
        return f'Error creating the database: {db_err}'
    except Exception as e:
        logging.error(f'Unexpected error during database creation: {e}')
        return f'Error creating the database: {e}'
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def validate_json_credentials(credentials):
    # List of required fields in the credentials
    required_fields = [
        'migType', 'oraSchema', 'oraHost', 'oraPort', 'oraPass', 'oraService',
        'pgDbName', 'pgHost', 'pgPort', 'pgPass', 'pgUser'
    ]
    
    # Check if any required fields are missing or have invalid values
    invalid_fields = [field for field in required_fields if not credentials.get(field)]
    
    # Log and return any fields that have None or empty values
    if invalid_fields:
        logging.error(f"Missing or null/empty values for fields: {', '.join(invalid_fields)}")
        return f"Missing or null/empty values for fields: {', '.join(invalid_fields)}"
    
    logging.info("All required fields are present and have valid values in the credentials.")
    return None  # Return None if all fields are valid

if __name__ == '__main__':
    try:
        private_ip = gsheet.get_private_ip()
        print(private_ip)
        all_credentials = gsheet.access_sheet()
        print(all_credentials)
                # List of required columns
        required_columns = ['Type','JBHost','JBPrivateIP','JBUsername','JBUserPwd', 'OraSchema', 'OraHost', 'OraPort', 'OraPass', 'OraService', 'PgDBName', 'PgHost', 'PgPort', 'PgPass', 'PgUser']

        # Validate required columns
        validate_columns_result = gsheet.validate_columns(all_credentials, required_columns)
        print(validate_columns_result)

        if validate_columns_result == 0:
            current_user = os.getenv('USERNAME')
            status_file_path = f'C:\\Users\\{current_user}\\Desktop\\migration_status\\credentials.json'
            gsheet.save_json_to_file(all_credentials,status_file_path)
            credentials = gsheet.load_credentials_from_json(private_ip)
            print(credentials)
            if credentials is not None:
                result_validate_json_credentials = validate_json_credentials(credentials)
                if result_validate_json_credentials is None:
                    createdb_result = create_database(credentials['migType'], credentials, 'templatedb')
                    print(f'createdb_result: {createdb_result}')
                    if createdb_result != 0:
                        status_update.update_status_in_file('P1', 'F', f'{createdb_result}')
                    else:
                        status_update.update_status_in_file('P1', 'O', 'Database setup done')
                else:
                    status_update.update_status_in_file('P1', 'F', f'{result_validate_json_credentials}')
            else:
                status_update.update_status_in_file('P1', 'F', f'No entry found for the remote host {private_ip} in json.')
        else:
            status_update.update_status_in_file('P1', 'F', f'{validate_columns_result}')

    except json.JSONDecodeError as json_err:
        logging.error(f'Error decoding JSON: {json_err}')
        print(f'An error occurred while processing the JSON data: {json_err}')
    except psycopg2.DatabaseError as db_err:
        logging.error(f'Database error occurred: {db_err}')
        print(f'A database error occurred: {db_err}')
    except Exception as e:
        logging.error(f'Unexpected error: {e}')
        print(f'An unexpected error occurred: {e}')