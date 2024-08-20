import os
import logging
import socket

log_dir = r'C:\Program Files\edb\prodmig\remote-mig-app\app\logs'
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=log_file_path, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
