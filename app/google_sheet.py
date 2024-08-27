import gspread
from oauth2client.service_account import ServiceAccountCredentials
import socket
import logging
import pandas as pd
import os
import time
from gspread.exceptions import APIError
import json

# Setting up logging
log_dir = r'C:\Program Files\edb\prodmig\remote-mig-app\app\logs'
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=log_file_path, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_private_ip():
    try:
        # Create a socket object to get the private IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        private_ip = s.getsockname()[0]
        s.close()
        return private_ip
    except Exception as e:
        logging.error(f'Failed to obtain private IP: {e}')
        return str(e)

def access_sheet(retries=10, wait_time=30):
    # Define the scope and credentials
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        r'C:\Program Files\edb\prodmig\remote-mig-app\app\project-remote-migration-app-d57c81bf8332.json', scope
    )
    client = gspread.authorize(creds)
    
    for attempt in range(retries):
        try:
            # Access the Google Sheet and fetch all records
            sheet = client.open('ginesys-remote-migration-sheet').sheet1
            data = sheet.get_all_records()
            df = pd.DataFrame(data)
            # Convert the DataFrame to a JSON string
            json_data = df.to_json(orient='records')
            return json_data
        
        except APIError as e:
            if "429" in str(e):
                logging.warning(f"Quota exceeded, retrying in {wait_time} seconds... (Attempt {attempt + 1} of {retries})")
                time.sleep(wait_time)
            else:
                logging.error(f"APIError occurred: {e}")
                raise
        except Exception as e:
            logging.error(f"An unexpected error occurred while accessing the sheet: {e}")
            raise
    raise Exception("Failed to access Google Sheet after several retries.")

def load_credentials_from_excel(excel_df, remoteip):
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
            logging.info(f"Credentials successfully loaded from Google Sheet for IP: {remoteip}")
        else:
            logging.warning(f"No entry found for the remote host {remoteip}")
    except Exception as e:
        logging.error(f"Error loading credentials from the Google Sheet: {e}")
    return credentials

def load_credentials_from_json(remoteip):
    try:
        with open(r"C:\Users\ginesysdevops\Desktop\migration_status\credentials.json", 'r') as jsonfile:
            content = json.load(jsonfile)
            for entry in content:
                if entry.get('PrivateIP') == remoteip:
                    credentials = {
                        'oraSchema': entry.get('OraSchema'),
                        'oraHost': entry.get('OraHost'),
                        'oraPort': entry.get('OraPort'),
                        'oraPass': entry.get('OraPass'),
                        'oraService': entry.get('OraService'),
                        'pgDbName': entry.get('PgDBName'),
                        'pgHost': entry.get('PgHost'),
                        'pgPort': entry.get('PgPort'),
                        'pgPass': entry.get('PgPass'),
                        'pgUser': entry.get('PgUser')
                    }
                    logging.info(f"Credentials successfully loaded from JSON for IP: {remoteip}")
                    return credentials
            logging.warning(f"No entry found for the remote host {remoteip}")
    except Exception as e:
        logging.error(f"Error loading credentials from the JSON file: {e}")
    return None

# Step 3: Save the JSON data to a file
def save_json_to_file(json_data, filename):
    try:
        with open(filename, 'w') as json_file:
            json_file.write(json_data)
        logging.info(f"JSON data successfully saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving JSON data to file: {e}")

if __name__ == "__main__":
    private_ip = get_private_ip()
    print(f"Private IP: {private_ip}")

    try:
        # Access Google Sheet and save the data to a JSON file
        json_data = access_sheet()
        save_json_to_file(json_data, r"C:\Users\ginesysdevops\Desktop\migration_status\credentials.json")

        # Load credentials based on the private IP address
        credentials = load_credentials_from_json(private_ip)
        
        if credentials:
            print(credentials)
            print("Credentials loaded successfully.")
        else:
            print("No credentials found for the given IP.")
    except Exception as e:
        logging.error(f"Failed to complete the operation: {e}")
        print("An error occurred. Please check the logs for more details.")
