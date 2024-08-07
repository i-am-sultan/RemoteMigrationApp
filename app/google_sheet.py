import gspread
from oauth2client.service_account import ServiceAccountCredentials
import socket
import logging
import pandas as pd

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
    creds = ServiceAccountCredentials.from_json_keyfile_name(r'project-remote-migration-app-d57c81bf8332.json')
    client = gspread.authorize(creds)
    sheet = client.open('ginesys-remote-migration-sheet').sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

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
    print(private_ip)

    excel_df = access_sheet()
    print(excel_df)