import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import socket
import logging
import pandas as pd

log_dir = os.getcwd()
log_file_path = os.path.join(log_dir,'logs',f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=log_file_path,filemode='a',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)

def get_private_ip():
    try:
        # create a socket object
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # connect to an external DNS server (Google's DNS server in this case)
        s.connect(("8.8.8.8", 80))
        # get the IP address of the current machine
        private_ip = s.getsockname()[0]
        # close the socket
        s.close()
        return private_ip
    except Exception as e:
        return str(e)
    
def access_sheet():
    # Define the scope
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(r'project-remote-migration-app-74f9c6a9bd41.json')
    client = gspread.authorize(creds)
    sheet = client.open('ginesys-remote-migration-sheet').sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

def update_sheet(remoteip,colname,message):
    # Define the scope
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(r'project-remote-migration-app-74f9c6a9bd41.json')
    client = gspread.authorize(creds)
    sheet = client.open('ginesys-remote-migration-sheet').sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Find the index of the row with the unique column value
    row_index = df[df['PrivateIP'] == remoteip].index[0]

    #Append with new status
    # existing_status = df.at[row_index,'Status']
    df.at[row_index,colname] = message
    # Convert the DataFrame back to a list of lists (to match gspread format)
    updated_data = [df.columns.values.tolist()] + df.values.tolist()    
    # Clear the existing sheet
    sheet.clear()
    # Update the sheet with the new data
    sheet.update(updated_data)

def load_credentials_from_excel(excel_df,remoteip):
    credentials = {}
    try:
        df = excel_df
        row = df[df['PrivateIP'] == remoteip]
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
            logging.info(f"Credentials successfully loaded from file Google Sheet \n{credentials}")
        else:
            logging.info(f"\nError: No entry found for the remote host {remoteip}")
    except Exception as e:
        logging.info(f'\nError loading credentials from the excel file: {e}')
    return credentials

if __name__ == "__main__":
    private_ip = get_private_ip()
    excel_df = access_sheet()
    update_sheet(private_ip,'Status','Updated')