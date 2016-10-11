import httplib2, os
from pathlib import Path

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

from runner import vars

flags = tools.argparser.parse_args(args=["--logging_level", "DEBUG"]) #these flags can be found at http://oauth2client.readthedocs.io/en/latest/source/oauth2client.tools.html#oauth2client.tools.run_flow. The following flag is not mentioned, but can be used as well --logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}

# If modifying these scopes, delete your previously saved credentials
# by running this script with the --new-credentials flag
SCOPES = 'https://www.googleapis.com/auth/drive'
APPLICATION_NAME = 'WPW Setup'

def get_credentials():
    """Gets user credentials from a stored credentials file.
    creates the file if it does not exist
    use the -v flag to recreate the credentials file
    """
    drive_dir = vars.storage_dir / 'google-drive'
    if not drive_dir.exists():
        drive_dir.mkdir()
    client_secret_loc = drive_dir / 'client_secret.json'

    store = oauth2client.file.Storage(str(client_secret_loc))
    if vars.new_credentials:
        try:
            store.delete() #if any changes are made to the client secret file, you'll need to delete the file so it can be recreated. The store.delete() command does this.
        except FileNotFoundError:
            pass

    if not client_secret_loc.exists():
        client_secret_contents = '''{
"installed": {
"client_id": "482103717697-qbfptkbld9gnb5vrfsal9h7csss8vejm.apps.googleusercontent.com",
"project_id": "pristine-lodge-142220",
"auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
"client_secret": "''' + vars.google_drive_client_secret + '''",
"redirect_uris": ["urn:ietf:wg:oauth:2.0:oob","http://localhost"],
"auth_uri": "https://accounts.google.com/o/oauth2/auth",
"token_uri": "https://accounts.google.com/o/oauth2/token"
}
}'''
        with client_secret_loc.open("w") as f:
            f.write(client_secret_contents)

    store = oauth2client.file.Storage('drive.storage')
    if vars.new_credentials:
        store.delete()
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(str(client_secret_loc), SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to {}'.format(client_secret_loc))
    return credentials

def list_drive_files(number_to_list=10):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    results = service.files().list(pageSize=number_to_list, fields="nextPageToken, files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        print('Files:')
        for item in items:
            print('{0} ({1})'.format(item['name'], item['id']))

def create_file(path, contents):
    raise Exception("this function isn't working right now :(")
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    file_metadata = {
      'name' : str(path),
      'mimeType' : 'application/vnd.google-apps.file',
      "action":"create",
      "folderId":"0ADK06pfg",
      "userId":"103354693083460731603"
    }
    file = service.files().create(body=file_metadata, fields='id').execute()
    return file

def get_file(file_id):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    return service.files().get_media(fileId=file_id).execute()

def create_folder(path):
    path = Path(path)
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    file_metadata = {
      'name' : str(path),
      'mimeType' : 'application/vnd.google-apps.folder'
    }
    file = service.files().create(body=file_metadata, fields='id').execute()
    if vars.verbose:
        print( 'Created Google Drive folder with the ID: %s' % file.get('id') )

    return file
