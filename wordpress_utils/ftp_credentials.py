'''
creates the .ftpass and and remote_sync.json files
'''
import os, sys
from runner import vars

def setup_remote_sync(server):
    """Sets up a folder so it can be used with remote sync atom plugin """

    ftp_host             = vars.servers[server]['host']
    ssh_username         = vars.servers[server]['ssh-username']
    ssh_password         = vars.servers[server]['ssh-password']
    ftp_username         = vars.servers[server]['ftp-username']
    ftp_password         = vars.servers[server]['ftp-password']

    remote_sync_file_contents = """
    {
      "uploadOnSave": true,
      "deleteLocal": false,
      "hostname": "web353.webfaction.com",
      "ignore": [
        ".remote-sync.json",
        ".git/**",
        "node_modules",
        "bower_components",
        ".sass-cache",
        ".ftppass"
      ],
      "transport": "scp",
      "target": """ + '"' + vars.servers_theme_dir + '"' + """,
      "username": """ + '"' + ssh_username + '"' + """,
      "password": """ + '"' + ssh_password + '"' + """
    }
    """

    with open(str(vars.project_dir) + '\\.remote-sync.json', 'w') as f:
        f.write(remote_sync_file_contents)

    ftppass_contents = """
    {
      "keyMain": {
        "user": '""" + ftp_username + """',
        "pass": '""" + ftp_password + """'
      }
    }
    """

    with open(str(vars.project_dir) + '\\.ftppass', 'w') as f:
        f.write(ftppass_contents)
