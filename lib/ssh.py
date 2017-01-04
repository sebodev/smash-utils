import subprocess
import os
import lib.servers
import lib.domains
from runner import vars
from pathlib import Path
from lib import webfaction

def get_command(*args, dont_execute=True, **kwargs):
    """ same as the run function, but returns the resulting ssh command instead of executing it """
    return run(*args, dont_execute=True, **kwargs)

def run(server, command, dont_execute=False, raise_errors=True, shell=True):
    """runs the ssh command, unless dont_execute is True, then the command is simply returned. The program will silently fail unless raise_errors=True."""
    if raise_errors and not dont_execute:
        subprocess.check_output(run(server, command, dont_execute=True, raise_errors=False, shell=shell))

    command = command.replace('""', '\\"')

    if server == "localhost" or server == "127.0.0.1":
        return command

    s = lib.servers.get(server)
    s_user = s["ssh-username"]
    s_host = s["host"]
    s_passwd = s["ssh-password"]
    s_name = server

    if os.name == "nt":
        if command:
            cmd = 'plink -ssh {s_user}@{s_host} -pw {s_passwd} "{command}"'.format(**locals())
        else:
            cmd = 'putty -ssh {s_user}@{s_host} -pw {s_passwd} "{command}"'.format(**locals())

        ssh_config = Path("~") / ".ssh" / "config"
        ssh_config = ssh_config.expanduser()
        if s_name and ssh_config.is_file() and s_name in ssh_config.read_text():

            #check if we have to use putty or if we already have ssh keys configured
            #Putty opens up in a new window which is annoying, so if ssh keys are already installed we use those,
            #otherwise, we use putty so that we can pass in the password on the command line
            cmd2 = "ssh -q -o ConnectTimeout=1 {s_name} exit".format(**locals())
            try:
                subprocess.check_output(cmd2) #this will fail if ssh keys are not setup
                cmd = 'ssh {s_name} "{command}"'.format(**locals())
            except subprocess.CalledProcessError:
                pass
    else:
        cmd = 'sshpass -p{s_passwd} ssh {s_user}@{s_host} "{command}"'.format(**locals())

    try:
        if dont_execute:
            subprocess.check_output("which putty") #make us raise an error if putty is not installed
            return cmd
        if vars.verbose:
            print("executing:", cmd)
        subprocess.run(cmd, shell=shell)
    except (FileNotFoundError, subprocess.CalledProcessError):
        #if putty is not installed, run the normal ssh command and the user will have to type in the password on the command line
        cmd = 'ssh {s_user}@{s_host} "{command}"'.format(**locals())
        if vars.verbose:
            print("nevermind, that command failed. Executing", cmd)
        print("use the password {s_passwd} when prompted".format(**locals()))

        if dont_execute:
            return cmd
        subprocess.run(cmd, shell=shell)
