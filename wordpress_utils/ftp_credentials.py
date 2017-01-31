'''
creates the .ftpass and and remote_sync.json files
'''
from pathlib import Path
import os, sys
from runner import vars
from lib import project_info

def setup_remote_sync(server, project, theme, user):
    """Sets up a folder so it can be used with remote sync atom plugin """

    ftp_host             = vars.servers[server]['host']
    ssh_username         = vars.servers[server]['ssh-username']
    ssh_password         = vars.servers[server]['ssh-password']
    ftp_username         = vars.servers[server]['ftp-username']
    ftp_password         = vars.servers[server]['ftp-password']

    info = project_info.info(project, theme, user)

    remote_sync_file_contents = """
    {
      "uploadOnSave": true,
      "deleteLocal": false,
      "hostname": """ + '"' + ftp_host.replace("\\", "\\\\") + '"' + """,
      "ignore": [
        ".remote-sync.json",
        ".git/**",
        "node_modules",
        "bower_components",
        ".sass-cache",
        ".ftppass"
      ],
      "transport": "scp",
      "target": """ + '"' + str(info["webfaction_theme_dir"]).replace("\\", "\\\\") + '"' + """,
      "username": """ + '"' + ssh_username.replace("\\", "\\\\") + '"' + """,
      "password": """ + '"' + ssh_password.replace("\\", "\\\\") + '"' + """
    }
    """

    with open(str(info["project_dir"]) + '\\.remote-sync.json', 'w') as f:
        f.write(remote_sync_file_contents)

    ftppass_contents = """
    {
      "keyMain": {
        "user": '""" + ftp_username + """',
        "pass": '""" + ftp_password + """'
      }
    }
    """

    with (Path(info["project_dir"]) / '.ftppass').open('w') as f:
        f.write(ftppass_contents)
