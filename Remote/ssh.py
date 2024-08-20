import paramiko

# Define SSH parameters
hostname = "172.30.4.12"
username = "ginesysdevops"
password = "GinDev#4321"
remote_script_path = r"C:\Program Files\edb\prodmig\remote-mig-app\app\main.py"

try:
    # Create an SSH client
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect to the remote server
    ssh_client.connect(hostname=hostname, username=username, password=password)

    # Execute the Python script on the remote server
    stdin, stdout, stderr = ssh_client.exec_command(f'python "{remote_script_path}" runall --mode drill')

    # Print the output and errors (if any)
    print(stdout.read().decode())
    print(stderr.read().decode())

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the SSH connection
    ssh_client.close()