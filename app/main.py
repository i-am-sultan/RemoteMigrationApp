import logging
import sys
import os
import socket
import sheet
import _1_credential_update as credupdate
import _2_version_compare as versioncomp
import _3_run_mig_app as runapp

migrationapp_path = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\RunEDBCommand.exe'

log_dir = os.getcwd()
log_file_path = os.path.join(log_dir,'logs',f'migration_log_{socket.gethostname()}.log')
logging.basicConfig(filename=log_file_path,filemode='a',format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)

if __name__ == '__main__':
    privateip = sheet.get_private_ip()
    excel_df = sheet.access_sheet()
    credentials = sheet.load_credentials_from_excel(excel_df,privateip)
    if sys.argv[1] == 'Process 1':
        result = credupdate.update_connections(credentials)
        if result:
            sheet.update_sheet(privateip,'Status','Credential updated successfully.')
        else:
            sheet.update_sheet(privateip,'Status',result)
    elif sys.argv[1] == 'Process 2':
        result = versioncomp.compare_versions(credentials)
        sheet.update_sheet(privateip,'VersionMatch',list(result)[0])

    elif sys.argv[1] == 'Process 3':
        result = runapp.run_mig_app(migrationapp_path,1)
        if result == 1:
            sheet.update_sheet(privateip,'Status','Migapp executed successfully')
        else:
            sheet.update_sheet(privateip,'Status',result)