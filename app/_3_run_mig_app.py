from sheet import *
import sys
import subprocess

migrationapp_path = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\RunEDBCommand.exe'

def run_mig_app(app_path,args):
    # command = [app_path] + [str(args)]
    command = app_path
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Output to terminal
        for line in process.stdout:
            print(line, end='')  # Print stdout line by line
            logging.info(line)

        # Capture stderr and output any errors
        stderr = process.stderr.read()
        if stderr:
            logging.error(f'Stderr from {app_path}:')
            logging.error(stderr)
            print(stderr, end='')

        # Wait for the process to complete
        process.wait()

        if process.returncode == 0:
            logging.info(f'{app_path} executed successfully.')
            return f'{app_path} executed successfully.'
        else:
            logging.error(f'{app_path} failed with return code {process.returncode}.')
            return f'{app_path} failed with return code {process.returncode}.'

    except Exception as e:
        logging.error(f'Error running {app_path}: {e}')
        print(f'{e}')
        return str(e)
    
if __name__ == '__main__':
    remoteip = get_private_ip()
    result = run_mig_app(migrationapp_path,1)
    update_sheet(remoteip,'Status',f"'{result}'")