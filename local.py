import winrm

def execute_script_remotely(remote_host, username, password, script_path):
    try:
        # Initialize WinRM session
        session = winrm.Session(remote_host, auth=(username, password), transport='basic')

        
        # Prepare the PowerShell command to execute the script
        ps_script = f'powershell.exe -ExecutionPolicy Bypass -File "{script_path}"'
        
        # Execute the command
        result = session.run_ps(ps_script)
        
        # Print the output and errors
        print("Output:")
        print(result.std_out.decode())
        if result.std_err:
            print("Errors:")
            print(result.std_err.decode())
        
    except winrm.exceptions.WinRMTransportError as e:
        print(f"Transport error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    remote_host = "http://vm-jumpbox-erp-stage-01.centralindia.cloudapp.azure.com:5985/wsman"  # Include WSMan port
    username = "ginesysdevops"
    password = "gmpl"
    script_path = r"C:\Users\sultan.m\Documents\Ginesys\RemoteMigrationApp\app\test.py"
    
    execute_script_remotely(remote_host, username, password, script_path)
