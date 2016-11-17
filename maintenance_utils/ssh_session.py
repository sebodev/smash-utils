import subprocess
import os
import lib.servers
import lib.domains
from runner import vars
from pathlib import Path
from lib import webfaction

def main(server_or_website):
    server = lib.servers.get(server_or_website, create_if_needed=False)
    app = None
    if not server:
        server, server_name, app = lib.domains.info(server_or_website)
        server_or_website = server_name
    if os.name == "nt":
        cmd = "putty -ssh {}@{} -pw {}".format(server["ssh-username"], server["host"], server["ssh-password"])

        ssh_config = Path("~") / ".ssh" / "config"
        ssh_config = ssh_config.expanduser()
        if ssh_config.is_file() and server_or_website in ssh_config.read_text():

            #check if we have to use putty or if we already have ssh keys configured
            #otherwise we use putty because unlike the ssh command putty allows us to input a password on the command line
            cmd2 = "ssh -q -o ConnectTimeout=1 {} exit".format(server_or_website)
            try:
                subprocess.check_output(cmd2)
                if app and webfaction.is_webfaction_server(server_or_website):
                    app_dir = webfaction.get_app_dir(server_or_website, app)
                    cmd = 'ssh -t {} "cd {} ; bash"'.format(server_or_website, app_dir)
                else:
                    cmd = "ssh {}".format(server_or_website)
            except subprocess.CalledProcessError:
                pass
    else:
        cmd = "sshpass -p{} ssh {}@{}".format(server["ssh-password"], server["ssh-username"], server["host"])

    try:
        if vars.verbose:
            print("executing:", cmd)
        subprocess.run(cmd)

    except FileNotFoundError:
        #if putty is not installed
        cmd = "ssh {}@{}".format(server["ssh-username"], server["host"])
        if vars.verbose:
            print("nevermind, that command failed. Executing", cmd)
        subprocess.run(cmd)
