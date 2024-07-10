import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QHeaderView
import paramiko

class MigrationApp(QWidget):
    def __init__(self, excel_file):
        super().__init__()

        self.excel_file = excel_file
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Automated Migration Application')

        layout = QVBoxLayout()

        # Load the Excel file
        self.df = pd.read_excel(self.excel_file)

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
        migration_script_path = r'C:\\Users\\sultan.m\\Desktop\\MigrationAutomation\\app\\scripts\\executor.py'

        try:
            # Establish SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname, username=username, password=password)
            print('connected...')

            # Execute the migration script
            exec_command = f'python {migration_script_path}'
            stdin, stdout, stderr = ssh.exec_command(exec_command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            if error:
                raise Exception(error)
            
            ssh.close()
            QMessageBox.information(self, 'Success', f'Connected to {hostname} and executed the script successfully.\nOutput:\n{output}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to connect to {hostname}.\nError: {str(e)}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    excel_file = r'C:\Users\sultan.m\Desktop\MigrationAutomation\app\scripts\PG Automation.xlsx'  # Path to your Excel file
    ex = MigrationApp(excel_file)
    ex.show()
    sys.exit(app.exec_())
