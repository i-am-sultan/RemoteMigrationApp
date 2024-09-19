import gspread
from oauth2client.service_account import ServiceAccountCredentials
import telnetlib
import socket

# Set up Google Sheets API
def get_google_sheet_data(sheet_url, sheet_name, column_name):
    # Define the scope for Google Sheets API
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Load credentials from your file (update the path to your credentials.json file)
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        r'C:\Program Files\edb\prodmig\remote-mig-app\app\project-remote-migration-app-d57c81bf8332.json', scope
    )
    client = gspread.authorize(creds)
    
    # Open the Google Sheet by URL
    sheet = client.open_by_url(sheet_url)
    worksheet = sheet.worksheet(sheet_name)
    
    # Get the header row (first row)
    header_row = worksheet.row_values(1)
    
    # Find the index of the column with the name 'OraHost'
    try:
        col_index = header_row.index(column_name) + 1  # +1 because gspread column indexing starts from 1
    except ValueError:
        print(f"Column '{column_name}' not found.")
        return []

    # Get all values from the column with the found index
    return worksheet.col_values(col_index)[1:]  # Skip the header row (first row)

# Telnet function
def check_telnet(ip, port):
    try:
        # Attempt to establish a connection using Telnet
        telnet = telnetlib.Telnet(ip, port, timeout=5)
        telnet.close()
        return "Success"
    except socket.timeout:
        return "Failed (Timeout)"
    except (socket.error, ConnectionRefusedError):
        return "Failed (Connection Refused)"
    except Exception as e:
        return f"Failed ({e})"

# Main function
if __name__ == "__main__":
    # Google Sheets details
    sheet_url = 'https://docs.google.com/spreadsheets/d/1FXaY0LVIkHZylWebz2URxX6APQxbf2qR4DDFFQ36Akc/edit?gid=616059585#gid=616059585'
    sheet_name = 'Main'  # Replace with your actual sheet name
    column_name = 'OraHost'  # Column header containing the Oracle host IPs

    # Fetch IPs from the Google Sheet
    ip_list = get_google_sheet_data(sheet_url, sheet_name, column_name)
    
    # Port number to check (1521 for Oracle DB)
    port = 1521

    # Loop over the list of IP addresses and check each one
    for ip in ip_list:
        if ip:
            result = check_telnet(ip, port)
            print(f"IP: {ip} - Connection: {result}")
    
    input("Press Enter to exit...")
