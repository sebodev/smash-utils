'''
creates the .ftpass and and remote_sync.json files
'''
import os, sys
from runner import vars

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
  "target": """ + '"' + vars.webfaction_theme_dir + '"' + """,
  "username": """ + '"' + vars.ssh_username + '"' + """,
  "password": """ + '"' + vars.ssh_password + '"' + """
}
"""

with open(str(vars.project_dir) + '\\.remote-sync.json', 'w') as f:
    f.write(remote_sync_file_contents)

ftppass_contents = """
{
  "keyMain": {
    "user": '""" + vars.ftp_username + """',
    "pass": '""" + vars.ftp_password + """'
  }
}
"""

with open(str(vars.project_dir) + '\\.ftppass', 'w') as f:
    f.write(ftppass_contents)
