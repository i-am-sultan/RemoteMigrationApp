import paramiko

def run_remote_script(hostname, port, username, password, remote_script_path):
    # Establish SSH connection
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port, username, password)

    # Enclose the remote script path in double quotes to handle spaces
    stdin, stdout, stderr = ssh.exec_command(f'python "{remote_script_path}"')

    # Read output and errors
    output = stdout.read().decode()
    errors = stderr.read().decode()

    # Close the connection
    ssh.close()

    return output, errors

if __name__ == "__main__":
    # Remote machine details
    hostname = '172.30.4.18'
    port = 22
    username = 'ginesysdevops'
    password = 'GinDev#4321'

    # Path to the existing script on the remote machine
    remote_script_path = r'C:\Program Files\edb\prodmig\remote-mig-app\app\cmdkey.py'

    # Run the script on the remote machine
    output, errors = run_remote_script(hostname, port, username, password, remote_script_path)

    print("Output:")
    print(output)
    print("Errors:")
    print(errors)
