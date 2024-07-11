import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView
import paramiko
import os
import socket

class MigrationApp(QWidget):
    def __init__(self, excel_file):
        super().__init__()

        self.excel_file = excel_file
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Automated Migration Application')

        # Set initial size of the window
        self.resize(900, 500)  # Width: 900 pixels, Height: 500 pixels

        layout = QVBoxLayout()

        # Load the Excel file
        try:
            self.df = pd.read_excel(self.excel_file)
        except FileNotFoundError:
            QMessageBox.critical(self, 'Error', f'Excel file not found: {self.excel_file}')
            return
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to load Excel file.\nError: {str(e)}')
            return

        # Create a QTableWidget
        self.table = QTableWidget()
        self.table.setRowCount(len(self.df))
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Remote Host', 'Username', 'Password', 'Action'])

        for index, row in self.df.iterrows():
            hostname = row['Hostname']
            username = row['Username']
            password = row['Password']

            self.table.setItem(index, 0, QTableWidgetItem(hostname))
            self.table.setItem(index, 1, QTableWidgetItem(username))
            self.table.setItem(index, 2, QTableWidgetItem(password))

            connect_button = QPushButton('Connect')
            connect_button.clicked.connect(lambda _, r=index: self.connect_to_host(r))
            self.table.setCellWidget(index, 3, connect_button)

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def connect_to_host(self, row):
        hostname = self.table.item(row, 0).text()
        username = self.table.item(row, 1).text()
        password = self.table.item(row, 2).text()
        shared_dir = r'Z:\\Remote\\'
        remote_dir = f'C:\\Users\\{username}\\Desktop\\Remote\\'
        current_host_path = f"{shared_dir}current_host.txt"
        with open(current_host_path,'w') as file:
            file.write(hostname)
        
        try:
            # Establish SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname, username=username, password=password)
            print('Connected...')

            try:
                # Create the directory if it does not exist
                stdin, stdout, stderr = ssh.exec_command(f'if not exist "{remote_dir}" mkdir "{remote_dir}"')
                error = stderr.read().decode()
                if error:
                    raise Exception(error)
            except Exception as e:
                raise Exception(f'Failed to create directory on remote host: {str(e)}')

            try:
                # Transfer each file in the shared directory to the remote directory
                sftp = ssh.open_sftp()
                for file_name in os.listdir(shared_dir):
                    local_file_path = os.path.join(shared_dir, file_name)
                    remote_file_path = os.path.join(remote_dir, file_name)
                    sftp.put(local_file_path, remote_file_path)
                sftp.close()
            except FileNotFoundError:
                raise Exception(f'Local file not found in directory: {shared_dir}')
            except Exception as e:
                raise Exception(f'Failed to transfer files to remote host: {str(e)}')
            
            remote_python_script_path = f"{remote_dir}executor.py"
            # Execute the migration script
            exec_command = f'python {remote_python_script_path}'
            stdin, stdout, stderr = ssh.exec_command(exec_command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            if error:

                raise Exception(error)
            
            ssh.close()
            QMessageBox.information(self, 'Success', f'Connected to {hostname} and executed the script successfully.\nOutput:\n{output}')
        except paramiko.AuthenticationException:
            QMessageBox.critical(self, 'Error', f'Authentication failed for {hostname}.')
        except paramiko.SSHException as e:
            QMessageBox.critical(self, 'Error', f'SSH error occurred while connecting to {hostname}.\nError: {str(e)}')
        except socket.error as e:
            QMessageBox.critical(self, 'Error', f'Network error occurred while connecting to {hostname}.\nError: {str(e)}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to connect to {hostname}.\nError: {str(e)}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    excel_file = r'Z:\\Remote\\PG Automation.xlsx'  # Path to your Excel file
    ex = MigrationApp(excel_file)
    ex.show()
    sys.exit(app.exec_())
