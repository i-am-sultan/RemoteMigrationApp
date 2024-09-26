Note:

change the credentials in schedule_jobs_in_postgres();
make sure to disable all the triggers in templatedb

How to start migration:

1. Fill all the required credentials in the google sheet(Make sure it's the clone oracle VM only, not live ones :( )
2. Turn on all the jumpboxes and source oracle VMs
3. Open the MasterVM exe 
4. Click on "Generate Script" -> Select the VMs -> Copy&Paste and run the scripts in admin Powershell
5. Click on "Test Connection" -> Click on "Update VMs" -> Check the updator logs in one jumpbox 
6. Click on "Run all" -> Click on "View Progress" -> Check the migration logs

How to update:

1. update the version file
2. commit and push changes first
3. make a zip of the app folder
4. publish a new release with the latest version
5. to check run the updator.py script

Steps:

P1: database creation, version check, credential update 
P2: edb, rowcomp
P3: postmig, audit
P4: dblink
P5: cube
P6: barcode ctrl file
P7: jobs
P8: report integration

Version 0.2.1: Barcode control incorporated.
Version 0.3.0: Report integration completed, credential.json formatted
Version 0.3.3: Azure bug workarround
Version 0.3.4: Live database dropping disabled. Migration type choosen from sheet only.
Version 0.3.9: Google sheet validation added.
Version 0.5.0: User dependencies removed.

Dependent Module:

pip install cachetools certifi charset-normalizer cx_Oracle filelock google-auth google-auth-oauthlib gspread httplib2 idna logging numpy oauth2client oauthlib pandas pip psycopg2 pyasn1 pyasn1_modules pyparsing python-dateutil pytz requests requests-oauthlib rsa six tzdata urllib3
