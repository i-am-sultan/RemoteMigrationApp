from sheet import *
import sys
import subprocess

migrationapp_path = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\RunEDBCommand.exe'

def run_mig_app(app_path,args):
    command = [app_path] + [args]
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True 
        )
        # Wait for the process to complete and get the output and error
        stdout, stderr = process.communicate()
        return stderr

    except Exception as e:
        logging.error(f'Error running {app_path}: {e}')
        return 0
    
if __name__ == '__main__':
    remoteip = get_private_ip()
    result = run_mig_app(migrationapp_path,1)
    if result == 1:
        update_sheet(remoteip,'Status','Migapp executed successfully')
    else:
        update_sheet(remoteip,'Status',result)