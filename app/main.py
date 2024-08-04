import logging
import sys
import os
import socket
import argparse
import sheet
import _1_credential_update as credupdate
import _2_version_compare as versioncomp
import _3_run_mig_app as runmigapp
import _4_run_audit_app as auditapp
import _5_run_mig_compare as comptool
import _6_run_postmig_patch as postmig
import _7_run_jobscript as jobs
import _8_run_postmig2_patch as postmig2

# Constants
MIGRATION_APP_PATH = r'C:\Program Files\edb\prodmig\RunCMDEdb_New\netcoreapp3.1\RunEDBCommand.exe'
AUDIT_TRIGGER_APP_PATH = r'C:\Program Files\edb\prodmig\AuditTriggerCMDNew\netcoreapp3.1\TriggerConstraintViewCreationForAuditPostMigration.exe'
COMPARE_TOOL_APP_PATH = r'C:\Program Files\edb\prodmig\Ora2PGCompToolKit\Debug\OraPostGreSqlComp.exe'
COMMON_POSTMIG_PATCH = r'C:\Program Files\edb\prodmig\PostMigPatches\postmigration.sql'

LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, f'migration_log_{socket.gethostname()}.log')

logging.basicConfig(
    filename=LOG_FILE_PATH,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    parser = argparse.ArgumentParser(description='Process migration and related tasks.')
    parser.add_argument('process', choices=[
        'Process 1', 'Process 2', 'Process 3', 'Process 4', 'Process 5', 
        'Process 6', 'Process 7', 'Process 8'
    ], help='The process to execute.')
    parser.add_argument('type', nargs='?', choices=['drill', 'live'], help='Type for Process 8.')

    args = parser.parse_args()

    # Check if 'Process 8' was selected but 'type' is not provided
    if args.process == 'Process 8' and args.type is None:
        parser.error("For 'Process 8', you must provide an additional 'type' argument. Choices are ['drill', 'live'].")

    try:
        privateip = sheet.get_private_ip()
        excel_df = sheet.access_sheet()
        credentials = sheet.load_credentials_from_excel(excel_df, privateip)

        if args.process == 'Process 1':
            result = credupdate.update_connections(credentials)
            status = 'Process 1:' + result
        elif args.process == 'Process 2':
            result = versioncomp.compare_versions(credentials)
            status = 'Process 2:' + result
        elif args.process == 'Process 3':
            result = runmigapp.run_mig_app(MIGRATION_APP_PATH, 1)
            status = 'Process 3:' + str(result)
        elif args.process == 'Process 4':
            result = auditapp.run_audit_app(AUDIT_TRIGGER_APP_PATH)
            status = 'Process 4:' + result
        elif args.process == 'Process 5':
            result = comptool.run_compare_tool(COMPARE_TOOL_APP_PATH)
            status = 'Process 5:' + result
        elif args.process == 'Process 6':
            result = postmig.execute_postmigration_script(credentials, COMMON_POSTMIG_PATCH)
            status = 'Process 6:' + result
        elif args.process == 'Process 7':
            result = jobs.createJobs(credentials)
            status = 'Process 7:' + result
        elif args.process == 'Process 8':
            if args.type.lower() == 'drill' or args.type.lower() == 'live':
                result = postmig2.execute_sql_patch(credentials, args.type)
                status = 'Process 8:' + result
            else:
                status = 'Wrong choice given to select postmigration type.'

        sheet.update_sheet(privateip, 'Status', f"'{status}'")
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
        sheet.update_sheet(privateip, 'Status', f"An error occurred: {e}")

if __name__ == '__main__':
    main()