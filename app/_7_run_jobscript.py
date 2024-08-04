import sheet
import psycopg2
import logging 
import os
import socket

log_dir = os.getcwd()
log_file_path = os.path.join(log_dir,'logs',f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=log_file_path,filemode='a',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)

def createJobs(credentials):
    pgHost = credentials['pgHost']
    pgPort = credentials['pgPort']
    pgUserName = credentials['pgUser']
    pgPass = credentials['pgPass']
    pgDbname = credentials['pgDbName']

    connection = None
    cursor = None
    try:
        # Connect to the PostgreSQL database and execute the job creation procedure.
        connection = psycopg2.connect(database='postgres', user=pgUserName, password=pgPass, host=pgHost, port=pgPort)
        cursor = connection.cursor()
        cursor.execute('call schedule_jobs_in_postgres()')
        connection.commit()
        logging.info(f'\nSuccessfully created jobs for the database {pgDbname}.')
        return f'\nSuccessfully created jobs for the database {pgDbname}.'
    except psycopg2.Error as e:
        logging.info(f'\nError creating jobs for the database {pgDbname}: {e}')
        return f'\nError creating jobs for the database {pgDbname}: {e}'
    except Exception as e:
        logging.info(f'\nUnexpected error while creating jobs for the database {pgDbname}: {e}')
        return f'\nUnexpected error while creating jobs for the database {pgDbname}: {e}'
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

if __name__ == "__main__":
    private_ip = sheet.get_private_ip()
    excel_df = sheet.access_sheet()
    credentials = sheet.load_credentials_from_excel(excel_df,private_ip)
    result = createJobs(credentials)
    sheet.update_sheet(private_ip,'Status',result)