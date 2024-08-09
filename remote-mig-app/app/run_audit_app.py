from google_sheet import *
from log_sheet import *
import os
import subprocess

audittriggerapp_path = r'C:\Program Files\edb\prodmig\AuditTriggerCMDNew\netcoreapp3.1\TriggerConstraintViewCreationForAuditPostMigration.exe'

# Logging Configuration
LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=LOG_FILE_PATH,filemode='a',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)

def run_audit_app(app_path):
    try:
        process = subprocess.run(
            app_path,
            check= True,
            capture_output= False,
            text= True
        )

        if process.returncode == 0:
            logging.info(f'{app_path} executed successfully.')
            return 0
        else:
            logging.error(f'{app_path} failed with return code {process.returncode}.')
            return f'{app_path} failed with return code {process.returncode}.'

    except Exception as e:
        logging.error(f'Error running {app_path}: {e}')
        print(f'{e}')
        return str(e)
    
if __name__ == '__main__':
    remoteip = get_private_ip()
    result = run_audit_app(audittriggerapp_path)
    print(result)
    update_sheet(remoteip,'Status',f"'{result}'")