'copies a theme from the webfaction server and readies the environment for dev use'


import subprocess, os, os.path
from runner import vars

def download(app, server, theme):
    #sometimes multiple themes will exist within a project. If this is the case we need to create the parent directory, otherwise the pscp command will fail.

    vars.change_current_project(app, theme)

    project_parent_dir = os.path.dirname(str(vars.project_dir))
    if not os.path.exists(project_parent_dir):
        os.makedirs(project_parent_dir)

    cmd = "pscp -scp -pw {} -r {}@{}:{} {}".format(vars.servers[server]['ftp-password'], vars.servers[server]['ftp-username'], vars.servers[server]['host'], vars.webfaction_theme_dir, vars.project_dir)
    if vars.verbose:
        print("running command: " + cmd)

    subprocess.check_call(cmd, shell=True)

    #subprocess.call(r"pscp -scp -i %UserProfile%\.ssh\sitesmash.ppk -r sebodev@webfaction:{} {}".format(vars.webfaction_theme_dir, vars.project_dir), shell=True)
    print( "copied {} to {}".format(vars.current_project, vars.project_dir) )
    print("configuring")
    from . import configure_project
    configure_project.setup(server)

def parse_args(args):

    try:
        app_name = args[0]
    except IndexError:
        app_name = None
    while not app_name:
        app_name = input('Enter the Webfaction app name: ')

    try:
        server = args[1]
    except IndexError:
        server = input('Enter a server entry. Leave blank to use the Sebodev Webfaction server: ')
        if not server:
            server = "sebodev"

    try:
        theme = args[2]
    except IndexError:
        from lib import webfaction
        wf, wf_id = webfaction.xmlrpc_connect(server)

        user = wf.system(wf_id, 'echo "$USER"')
        cmd = "ls /home/{}/webapps/{}/wp-content/themes/".format(user, app_name)
        themes = wf.system(wf_id, cmd)
        themes = themes.replace("index.php", "")
        print("possible theme names are: "+themes)


        theme = None
        while not theme:
            theme = input("Which theme would you like to download: ")

    download(app_name, server, theme)
