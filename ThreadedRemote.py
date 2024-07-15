import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView
import paramiko
import os
import socket
from PyQt5.QtCore import QThread, pyqtSignal

class SSHWorker(QThread):
    result = pyqtSignal(str, str)  # Signal to send the result back to the main thread

    def __init__(self, hostname, username, password, shared_dir, remote_dir, parent=None):
        super(SSHWorker, self).__init__(parent)
        self.hostname = hostname
        self.username = username
        self.password = password
        self.shared_dir = shared_dir
        self.remote_dir = remote_dir

    def run(self):
        try:
            # Establish SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.hostname, username=self.username, password=self.password)
            print('Connected...')

            try:
                # Create the directory if it does not exist
                stdin, stdout, stderr = ssh.exec_command(f'if not exist "{self.remote_dir}" mkdir "{self.remote_dir}"')
                error = stderr.read().decode()
                if error:
                    raise Exception(error)
            except Exception as e:
                raise Exception(f'Failed to create directory on remote host: {str(e)}')

            try:
                # Transfer each file in the shared directory to the remote directory
                sftp = ssh.open_sftp()
                for file_name in os.listdir(self.shared_dir):
                    local_file_path = os.path.join(self.shared_dir, file_name)
                    remote_file_path = os.path.join(self.remote_dir, file_name)
                    sftp.put(local_file_path, remote_file_path)
                sftp.close()

            except FileNotFoundError:
                raise Exception(f'Local file not found in directory: {self.shared_dir}')
            except Exception as e:
                raise Exception(f'Failed to transfer files to remote host: {str(e)}')
            remote_python_script_path = f"{self.remote_dir}executor.py"
            # Execute the migration script
            exec_command = f'python {remote_python_script_path}'
            stdin, stdout, stderr = ssh.exec_command(exec_command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            if error:
                raise Exception(error)
            
            ssh.close()
            self.result.emit('Success', f'Connected to {self.hostname} and executed the script successfully.\nOutput:\n{output}')
        except paramiko.AuthenticationException:
            self.result.emit('Error', f'Authentication failed for {self.hostname}.')
        except paramiko.SSHException as e:
            self.result.emit('Error', f'SSH error occurred while connecting to {self.hostname}.\nError: {str(e)}')
        except socket.error as e:
            self.result.emit('Error', f'Network error occurred while connecting to {self.hostname}.\nError: {str(e)}')
        except Exception as e:
            self.result.emit('Error', f'Failed to connect to {self.hostname}.\nError: {str(e)}')

class MigrationApp(QWidget):
    def __init__(self, excel_file):
        super().__init__()
        self.excel_file = excel_file
        self.initUI()
    def initUI(self):
        self.setWindowTitle('Automated Migration Application')
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

        self.worker = SSHWorker(hostname, username, password, shared_dir, remote_dir)
        self.worker.result.connect(self.handle_result)
        self.worker.start()

    def handle_result(self, status, message):
        if status == 'Success':
            QMessageBox.information(self, 'Success', message)
        else:
            QMessageBox.critical(self, 'Error', message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    excel_file = r'Z:\\Remote\\PG Automation.xlsx'  # Path to your Excel file
    ex = MigrationApp(excel_file)
    ex.show()
    sys.exit(app.exec_())
