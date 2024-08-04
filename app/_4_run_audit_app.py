from sheet import *
import sys
import subprocess


audittriggerapp_path = r'C:\Program Files\edb\prodmig\AuditTriggerCMDNew\netcoreapp3.1\TriggerConstraintViewCreationForAuditPostMigration.exe'

def run_audit_app(app_path):
    try:
        process = subprocess.Popen(
            app_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # Wait for the process to complete and get the output and error
        stdout, stderr = process.communicate()
        
        if stdout:
            logging.info(f'Stdout from {app_path}:')
            logging.info(stdout)
            if stderr:
                logging.error(f'Stderr from {app_path}:')
                logging.error(stderr)
                return stderr + stdout
        else:
            logging.info(f'{app_path} executed successfully.')
            return f'{app_path} executed successfully.'

    except Exception as e:
        logging.error(f'Error running {app_path}: {e}')
        return e
    
if __name__ == '__main__':
    remoteip = get_private_ip()
    result = run_audit_app(audittriggerapp_path)
    print(result)
    update_sheet(remoteip,'Status',f"'{result}'")