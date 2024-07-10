import paramiko

# Define the connection details
hostname = '10.70.1.16'
# hostname = '127.0.0.1'
port = 22
username = 'sultan.m'
password = 'Sltn#54321'  # You may want to use key-based authentication instead for security
# password = 'Gsl#4321'  # You may want to use key-based authentication instead for security

# Define the command to run
file_path = r'C:\Users\sultan.m\Desktop\MigrationAutomation\GinesysMigApp\runMigraionApp.bat'
file_path = r'C:\Users\sultan.m\Desktop\abc.txt'
command = f'cmd /c {file_path}'

# Create an SSH client
client = paramiko.SSHClient()
# Automatically add the server's host key (use with caution)
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    # Connect to the server
    client.connect(hostname, port, username, password)
    print('connected...') 
    #make sure you have started the service...
    #To start ther service Run Powershell in admin and type "Start-Service sshd" and check status using "Get-Service sshd"
    # Execute the command
    stdin, stdout, stderr = client.exec_command(command)
    # Read and print the output
    print(stdout.read().decode())
    print(stderr.read().decode())
finally:
    # Close the connection
    client.close()