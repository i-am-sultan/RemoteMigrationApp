import os
import logging
import socket
import sys
current_user = os.getenv('USERNAME')

log_dir = f'C:\\Users\\{current_user}\\Desktop\\migration_status'

file = f'test_{socket.gethostname()}.log'

with open(file,'w') as f1:
    content = f1.write('Content:')

log_file_path = os.path.join(log_dir,f'test_{socket.gethostname()}.log')
logging.basicConfig(filename=log_file_path,filemode='a',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)

def run():
    if 1==1:
        hostname = socket.gethostname()
        logging.info(f'logging succesfull: hostname = {hostname}')

if __name__ == '__main__':
    run()