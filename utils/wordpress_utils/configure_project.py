'''used to configure projects
so that the smash --watch command will be able to keep the project
in sync with webfaction.
'''

import subprocess, os, sys
from pathlib import Path
import os.path
from runner import smash_vars
from lib import project_info

def setup(server, project, theme, user):
    setup_remote_sync(server, project, theme, user)
    info = project_info.info(project, theme, user)

    os.chdir(str(info["project_dir"]))
    npm_packages = Path(info["project_dir"]) / "packages.json"
    if npm_packages.exists():
        subprocess.call("npm start", shell=True, cwd=info["project_dir"])
    elif smash_vars.verbose:
        print("Could not find the file %s. Skipping the npm installation. If this theme was not based off the undescores theme, this is ok." % npm_packages)
    print('-' * 80)
    print("\nCreated project for %s. Happy coding.\n" % project)

def setup_remote_sync(server, project, theme, user):
    """Add files to a directory to make it usable with the remote sync atom plugin """

    ftp_host             = smash_vars.servers[server]['host']
    ssh_username         = smash_vars.servers[server]['ssh-username']
    ssh_password         = smash_vars.servers[server]['ssh-password']
    ftp_username         = smash_vars.servers[server]['ftp-username']
    ftp_password         = smash_vars.servers[server]['ftp-password']

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
