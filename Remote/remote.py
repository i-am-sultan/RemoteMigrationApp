import sys
import json
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QComboBox, QMessageBox, QDialog, QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import paramiko

# Configure logging
logging.basicConfig(
    filename='migration_dashboard.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filemode='a'
)

logger = logging.getLogger(__name__)

# Google Sheets Setup
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = r'C:\Users\sultan.m\Documents\Ginesys\RemoteMigrationApp\Remote\project-remote-migration-app-d57c81bf8332.json'
SPREADSHEET_NAME = 'ginesys-remote-migration-sheet'

def run_command_ssh(hostname, username, password, command):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()
        return output, error
    except Exception as e:
        return str(e), None

def connect_to_google_sheet():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open(SPREADSHEET_NAME).sheet1
        logger.info("Connected to Google Sheets successfully.")
        return sheet
    except Exception as e:
        logger.error(f"Failed to connect to Google Sheets: {str(e)}")
        sys.exit("Could not connect to Google Sheets")

# Worker class for threading
class Worker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    update_progress = pyqtSignal(str)

    def __init__(self, command, private_ip, username, password, task=""):
        super().__init__()
        self.command = command
        self.private_ip = private_ip
        self.username = username
        self.password = password
        self.task = task

    def run(self):
        try:
            print(f'command: {self.command}')
            output, error = run_command_ssh(self.private_ip, self.username, self.password, self.command)
            if self.task == "view_progress":
                self.update_progress.emit(output)
            else:
                if error:
                    raise Exception(error)
                # self.finished.emit(f"Command executed successfully on {self.private_ip}")
                logger.info(f"Command executed successfully on {self.private_ip}")
        except Exception as e:
            error_message = f"Failed to execute command on {self.private_ip}\n{str(e)}"
            logger.error(error_message)
            self.error.emit(error_message)


# PyQt5 Dialog for Progress
class ProgressDialog(QDialog):
    def __init__(self, progress_content, parent=None):
        super().__init__(parent)
        self.setWindowTitle("View Progress")
        self.setGeometry(200, 200, 600, 400)  # Adjusted size for better readability
        layout = QVBoxLayout()

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(self.format_progress_content(progress_content))

        layout.addWidget(self.text_edit)
        self.setLayout(layout)

    def format_progress_content(self, content):
        """Format JSON content for display."""
        try:
            # Ensure the content is a valid string
            if isinstance(content, str):
                data = json.loads(content)
            else:
                return "Error: Content is not a string."

            process = data.get("Process", "N/A")
            status = data.get("Status", "N/A")
            message = data.get("Message", "")

            formatted_message = (
                f"Process: {process}\n"
                f"Status: {'Failure' if status == 'F' else 'Success'}\n\n"
                f"Details:\n{message}"
            )
            return formatted_message
        except json.JSONDecodeError:
            return "Error: Failed to decode JSON content."
        except Exception as e:
            return f"Error: {str(e)}"

# PyQt5 Dashboard
class MigrationDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.sheet = connect_to_google_sheet()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Bulk Migration Dashboard")
        self.setGeometry(100, 100, 1400, 600)

        layout = QVBoxLayout()

        self.table = QTableWidget(self)
        self.table.setRowCount(len(self.sheet.get_all_records()))
        self.table.setColumnCount(7)  # Hostname, PrivateIP, Connect, Step, Migration Type, Run, View Progress
        self.table.setHorizontalHeaderLabels(["Hostname", "PrivateIP", "Connect", "Step", "Migration Type", "Run", "View Progress"])

        self.populate_table()

        layout.addWidget(self.table)
        self.setLayout(layout)

    def populate_table(self):
        try:
            records = self.sheet.get_all_records()
            for i, record in enumerate(records):
                hostname_item = QTableWidgetItem(record['Hostname'])
                privateip_item = QTableWidgetItem(record['PrivateIP'])

                connect_button = QPushButton('Connect')
                connect_button.clicked.connect(lambda _, row=i: self.connect_to_vm(row))

                step_combo = QComboBox(self)
                step_combo.addItems(['runall', 'runpostmig', 'runfinalmig', 'runjobs'])

                migration_type_combo = QComboBox(self)
                migration_type_combo.addItems(['drill', 'live'])

                run_button = QPushButton('Run')
                run_button.clicked.connect(lambda _, row=i: self.run_migration(row))

                view_progress_button = QPushButton('View Progress')
                view_progress_button.clicked.connect(lambda _, row=i: self.view_progress(row))

                self.table.setItem(i, 0, hostname_item)
                self.table.setItem(i, 1, privateip_item)
                self.table.setCellWidget(i, 2, connect_button)
                self.table.setCellWidget(i, 3, step_combo)
                self.table.setCellWidget(i, 4, migration_type_combo)
                self.table.setCellWidget(i, 5, run_button)
                self.table.setCellWidget(i, 6, view_progress_button)

            logger.info("Table populated successfully.")
        except Exception as e:
            logger.error(f"Failed to populate table: {str(e)}")

    def get_credentials(self, row, credential_set):
        """Retrieve credentials based on selected set."""
        record = self.sheet.get_all_records()[row]
        username = record.get('Username', '')
        password = record.get('Password', '')
        return {
            'username': username,
            'password': password
        }

    def connect_to_vm(self, row):
        private_ip = self.sheet.cell(row + 2, 2).value
        credentials = self.get_credentials(row, 'Username')
        username = credentials['username']
        password = credentials['password']
        command = r'python "C:\Program Files\edb\prodmig\remote-mig-app\app\test.py"'
        logger.info(f"Attempting to connect to {private_ip} as {username}")
        self.run_in_thread(command, private_ip, username, password)



    def run_migration(self, row):
        private_ip = self.sheet.cell(row + 2, 2).value
        credentials = self.get_credentials(row, 'Username')
        username = credentials['username']
        password = credentials['password']
        step = self.table.cellWidget(row, 3).currentText()
        migration_type = self.table.cellWidget(row, 4).currentText()
        command = (f'python "C:\\Program Files\\edb\\prodmig\\remote-mig-app\\app\\main.py" {step} --mode {migration_type}')
        print(command)
        logger.info(f"Running migration on {private_ip} with step '{step}' and mode '{migration_type}'")
        self.run_in_thread(command, private_ip, username, password)


    def view_progress(self, row):
        private_ip = self.sheet.cell(row + 2, 2).value
        credentials = self.get_credentials(row, 'Username')
        username = credentials['username']
        password = credentials['password']
        # Adjust command for Windows paths and quoting
        command = 'type "C:\\Users\\ginesysdevops\\Desktop\\migration_status\\status.json"'
        logger.info(f"Viewing progress for {private_ip}")
        self.run_in_thread(command, private_ip, username, password, task="view_progress")


    def run_in_thread(self, command, private_ip, username, password, task=""):
        """Run command in a separate thread."""
        self.worker = Worker(command, private_ip, username, password, task)
        if task == "view_progress":
            self.worker.update_progress.connect(self.show_progress_dialog)
        else:
            self.worker.finished.connect(self.on_success)
            self.worker.error.connect(self.on_failure)
        self.worker.start()

    def show_progress_dialog(self, progress_content):
        """Display the progress content in a dialog."""
        try:
            # Debugging: Print the raw content to check if it's valid JSON
            logger.info(f"Raw progress content: {progress_content}")

            dialog = ProgressDialog(progress_content, self)
            dialog.exec_()
        except Exception as e:
            logger.error(f"Failed to show progress dialog: {str(e)}")


    def on_success(self, message):
        logger.info(message)
        QMessageBox.information(self, "Success", message)

    def on_failure(self, message):
        logger.error(message)
        QMessageBox.critical(self, "Failure", message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MigrationDashboard()
    ex.show()
    sys.exit(app.exec_())
