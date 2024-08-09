import psycopg2
import logging 
import os 
import socket
import google_sheet as gsheet

# Logging Configuration
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=log_file_path, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def check_if_exists_samedb(credentials):
    pgHost = credentials['pgHost']
    pgPort = credentials['pgPort']
    pgUserName = credentials['pgUser']
    pgPass = credentials['pgPass']
    pgDbname = credentials['pgDbName'] 

    query = 'SELECT 1 FROM pg_database WHERE datname = %s;'
    connection = None
    cursor = None
    
    try:
        # Connect to the default 'postgres' database to check for existence
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
    except Exception as e:
        logging.error(f'Error checking database existence: {e}')
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def terminate_connections(credentials,source_db):
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
        # Connect to the default 'postgres' database to terminate connections
        connection = psycopg2.connect(database='postgres', user=pgUserName, password=pgPass, host=pgHost, port=pgPort)
        cursor = connection.cursor()
        cursor.execute(query, (source_db,))
        connection.commit()
        logging.info(f'All connections to database "{source_db}" have been terminated.')
    except Exception as e:
        logging.error(f'Error terminating connections: {e}')
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def create_database(credentials,source_db):
    pgHost = credentials['pgHost']
    pgPort = credentials['pgPort']
    pgUserName = credentials['pgUser']
    pgPass = credentials['pgPass']
    pgDbname = credentials['pgDbName']

    if check_if_exists_samedb(credentials):
        logging.info('Database creation skipped because the database already exists.')
        return 0

    # Terminate other connections to the database
    terminate_connections(credentials,source_db)

    content = f'''CREATE DATABASE "{pgDbname}"
                WITH
                OWNER = gslpgadmin
                ENCODING = 'UTF8'
                LC_COLLATE = 'C'
                LC_CTYPE = 'C'
                LOCALE_PROVIDER = 'libc'
                --TABLESPACE = pg_default
                CONNECTION LIMIT = -1
                TEMPLATE = {source_db}'''

    connection = None
    
    try:
        # Connect to the default 'postgres' database to create a new database
        connection = psycopg2.connect(database='postgres', user=pgUserName, password=pgPass, host=pgHost, port=pgPort)
        connection.autocommit = True  # Disable transaction block
        cursor = connection.cursor()
        cursor.execute(content)
        cursor.execute(f'''  ALTER DATABASE "{pgDbname}"
                                SET search_path TO main, public, gateway, ginview, ginarchive;
                            ALTER DATABASE "{pgDbname}"
                                SET "TimeZone" TO 'Asia/Kolkata';''')
        logging.info(f'Database "{pgDbname}" created successfully.')
        return 0
    except Exception as e:
        logging.error(f'Error creating database: {e}')
        return f'Error creating database: {e}'
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == '__main__':
    try:
        private_ip = gsheet.get_private_ip()
        all_credentials = gsheet.access_sheet()
        credentials = gsheet.load_credentials_from_excel(all_credentials, private_ip)
        source_db = 'maintenance_dev'
        db_creation_result = create_database(credentials,source_db)
        print(db_creation_result)
    except Exception as e:
        logging.error(f'Unexpected error: {e}')
        print(f'An unexpected error occurred: {e}')