import pandas as pd
import socket
import os 
import logging
from filelock import FileLock

def get_private_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        private_ip = s.getsockname()[0]
        s.close()
        return private_ip
    except Exception as e:
        return str(e)

def update_sheet(remoteip, colname, message):
    log_sheet = r'Z:\Remote\Log\migration_log_sheet.xlsx'
    lock_file = log_sheet + '.lock'
    
    try:
        # Acquire a file lock
        with FileLock(lock_file):
            # Convert the excel sheet into pandas DataFrame
            df = pd.read_excel(log_sheet, engine='openpyxl')

            if 'PrivateIP' not in df.columns:
                raise KeyError("Missing column 'PrivateIP' in excel")

            matching_rows = df[df['PrivateIP'] == remoteip]
            if matching_rows.empty:
                print(f"No matching rows found for the IP: {remoteip}")
                return

            row_index = matching_rows.index[0]
            df.at[row_index, colname] = message

            df.to_excel(log_sheet, index=False, engine='openpyxl')
            print(f"Updated {colname} for IP {remoteip} with message '{message}'.")
    except KeyError as ke:
        print(f"KeyError: {ke}")
    except FileNotFoundError:
        print(f"FileNotFoundError: The file {log_sheet} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    privateip = get_private_ip()
    print(f"Private IP: {privateip}")
    update_sheet(privateip, 'Status', 'Checking')