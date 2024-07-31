import os
import logging
import socket

log_dir = os.getcwd()

file = f'migration_log_{socket.gethostname()}.log'
with open(file,'w') as f1:
    content = f1.write('Content:')
log_file_path = os.path.join(log_dir,'logs',f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=log_file_path,filemode='a',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)

def run(user_imput):
    if 1==1:
        hostname = socket.gethostname()
        logging.info(f'logging succesfull, here is process name {user_imput}')

if __name__ == '__main__':
    user_imput = input('Enter a value:')
    run(user_imput)