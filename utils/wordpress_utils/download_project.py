'copies a theme from the webfaction server and readies the environment for dev use'

import subprocess, os, os.path
from pathlib import Path

from runner import smash_vars
from lib import project_info
from lib import webfaction
from lib import servers
from lib import domains
from lib import project_info

def main(site, theme):

    _, server, app_name = domains.info(site)

    if not server:
        server = input('Enter a server entry. Leave blank to use the wpwarranty Webfaction server: ')
        if not server:
            server = "wpwarranty"

    while not app_name:
        app_name = input('Enter the Webfaction app name: ')

    if not theme:
        wf, wf_id = webfaction.connect(server)

        user = wf.system(wf_id, 'echo "$USER"')
        cmd = "ls /home/{}/webapps/{}/wp-content/themes/".format(user, app_name)
        themes = wf.system(wf_id, cmd)
        themes = themes.replace("\nindex.php", "")

        cmd = "ls /home/{}/webapps/{}/wp-content/plugins/".format(user, app_name)
        plugins = wf.system(wf_id, cmd)
        plugins = plugins.replace("\nindex.php", "")

        print("possible theme names are: \n"+themes)
        print("\npossible plugin names are: \n"+plugins)


        theme = None
        while not theme:
            theme = input("\nWhich theme/plugin would you like to download: ")

    download(server, app_name, theme)

def download(server, app, theme_or_plugin):
    """ downloads a theme or plugin from a webfaction server. """

    theme = theme_or_plugin

    info = project_info.info(app, theme, webfaction.get_user(server))
    info.update(servers.get(server))

    project_parent_dir = os.path.dirname(info["project_dir"])
    if not os.path.exists(project_parent_dir):
        os.makedirs(project_parent_dir)

    wf, wf_id = webfaction.connect(server)
    cmd = "ls /home/{}/webapps/{}/wp-content/plugins/".format(info["user"], app)
    #using wf.system of over lib.ssh so we can capture the output
    plugins = wf.system(wf_id, cmd).split("\n")
    remote_dir = (os.path.join(info["webfaction_plugins_dir"],theme)) if theme in plugins else str(info["webfaction_theme_dir"])

    cmd = "pscp -scp -pw {} -r {}@{}:{} {}".format(info['ftp-password'], info['ftp-username'], info['host'], remote_dir, info["project_dir"])
    if smash_vars.verbose:
        print("running command: " + cmd)

    subprocess.check_call(cmd, shell=True)

    #subprocess.call(r"pscp -scp -i %UserProfile%\.ssh\sitesmash.ppk -r sebodev@webfaction:{} {}".format(smash_vars.servers_theme_dir, smash_vars.project_dir), shell=True)
    print( "copied {} to {}".format(info["project"], info["project_dir"]) )
    print("configuring")
    from . import configure_project
    configure_project.setup(server, info["project"], theme_or_plugin, info["user"])
