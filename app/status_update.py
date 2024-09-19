import logging
import json

def update_status_in_file(process_id, status, status_message):
    filepath = r'C:\Users\ginesysdevops\Desktop\migration_status\status.json'
    # filepath = r'C:\Users\sultan.m\Desktop\migration_status\status.json'
    try:
        with open(filepath,'r') as file:
            content = json.load(file)
            content["Process"] = process_id
            content["Status"] = status
            content["Message"] = status_message
        with open(filepath,'w') as f:
            json.dump(content,f,indent=4)
        logging.info(f'Status updated in status.json')
    except FileNotFoundError:
        logging.error(f'Error: File {filepath} not found.')
    except json.JSONDecodeError as e:
        logging.error(f'Error decoding JSON from {filepath}: {e}', exc_info=True)
    except Exception as e:
        logging.error(f'Error updating config.json: {e}', exc_info=True)

def update_status_in_file_for_postmigration(process_id, status, status_message, postmigration_status):
    filepath = r'C:\Users\ginesysdevops\Desktop\migration_status\status.json'
    try:
        with open(filepath,'r') as file:
            content = json.load(file)
            content["Process"] = process_id
            content["Status"] = status
            content["Message"] = status_message
            content["Postmig_Status"] = postmigration_status
        with open(filepath,'w') as f:
            json.dump(content,f,indent=4)
        logging.info(f'Status updated in status.json')
    except FileNotFoundError:
        logging.error(f'Error: File {filepath} not found.')
    except json.JSONDecodeError as e:
        logging.error(f'Error decoding JSON from {filepath}: {e}', exc_info=True)
    except Exception as e:
        logging.error(f'Error updating config.json: {e}', exc_info=True)

if __name__ == '__main__':
    update_status_in_file('P','O','checking..') 