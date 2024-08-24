import socket
import logging
import os
import requests
import zipfile
from io import BytesIO

# Logging Configuration
LOG_DIR = os.path.join(os.getcwd(), 'logs')
# LOG_DIR = r'C:\Program Files\edb\prodmig\remote-mig-app\app\logs'

os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, f'updator_log_{socket.gethostname()}.log')

logging.basicConfig(filename=LOG_FILE_PATH, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

def get_latest_release_info(repo):
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    headers = {
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        release_info = response.json()
        return release_info
    else:
        print(f"Failed to fetch release information. Status code: {response.status_code}")
        return None

def checkForUpdates():
    logging.info('Checking for updates...')
    try:
        repo = "i-am-sultan/RemoteMigrationApp"
        latest_release = get_latest_release_info(repo)

        if latest_release:
            latest_version = latest_release['tag_name']
            assets = latest_release['assets']

            if assets:
                os.chdir('..')  # RemoteMigrationApp directory
                version_path = os.path.join(os.getcwd(), 'app', 'version.txt')

                # Read the current version from a file
                try:
                    with open(version_path, 'r') as f:
                        current_version = f.read().strip()
                except Exception as e:
                    logging.info(f'Failed to read the current version. Error: {e}')
                    return 1

                logging.info(f'Current version: {current_version}')
                logging.info(f'Latest version: {latest_version}')

                # Compare versions
                if latest_version != current_version:
                    logging.info('New version available. Downloading and applying updates...')

                    for asset in assets:
                        update_url = asset['browser_download_url']
                        asset_name = asset['name']

                        # Download the update
                        response = requests.get(update_url)
                        if response.status_code == 200:
                            try:
                                if asset_name == 'app.zip':
                                    update_dir_path = os.getcwd()  # cwd: RemoteMigrationApp

                                    # Extract the zip file into the app directory
                                    with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
                                        zip_ref.extractall(update_dir_path)

                                    logging.info(f'{asset_name} downloaded and extracted successfully to the app directory.')

                                elif asset_name == 'VMExecutionTest.zip':
                                    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')

                                    # Extract the zip file into the desktop
                                    with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
                                        zip_ref.extractall(desktop_path)

                                    logging.info(f'{asset_name} downloaded and extracted successfully to the Desktop.')

                                else:
                                    logging.info(f'Unknown asset {asset_name}. Skipping extraction.')

                            except Exception as e:
                                logging.info(f'Failed to extract and apply update for {asset_name}. Error: {e}')
                                return f'Failed to extract and apply update for {asset_name}. Error: {e}'
                        else:
                            logging.info(f"Failed to download {asset_name}. Status code: {response.status_code}")
                            return f"Failed to download {asset_name}. Status code: {response.status_code}"

                    logging.info('All updates downloaded and extracted successfully.')
                    return 0

                else:
                    logging.info('You are already using the latest version.')
                    return 'You are already using the latest version.'
            else:
                logging.info('No assets found in the latest release.')
                return 'No assets found in the latest release.'
        else:
            logging.info('Failed to fetch latest release information.')
            return 'Failed to fetch latest release information.'

    except Exception as e:
        logging.info(f'Error checking and applying updates: {e}')
        return f'Error checking and applying updates: {e}'

if __name__ == '__main__':
    os.chdir(r'C:\Program Files\edb\prodmig\remote-mig-app\updator')
    print(os.getcwd())
    result = checkForUpdates()
    version_path = os.getcwd()
    if result == 0:
        print(f'Updated! Now close this application! Run the latest version!\nCheck the latest version in directory: {version_path}')
    else:
        print(result)
