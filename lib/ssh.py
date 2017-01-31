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

    command = command.replace('"', '\\"')

    if "localhost" in lib.servers.get(server, "domains") or "127.0.0.1" in lib.servers.get(server, "domains"):
        if vars.verbose:
            print("executing:", command)
        if dont_execute:
            return command
        subprocess.run(command, shell=shell)
        return

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
            #raise an error so we can return enter the except clause and return the alternate ssh command if putty is not installed
            subprocess.check_output("which putty")
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

#This time I return the output.
def run2(server, command, shell=True):
    """Determines the best method for running an SSH command, and then runs it, returning the ouput as a string.
    If anything is outputted to stderr, an error is raised. """

    command = command.replace('"', '\\"')

    if "localhost" in lib.servers.get(server, "domains") or "127.0.0.1" in lib.servers.get(server, "domains"):
        if vars.verbose:
            print("executing:", command)
        stdout_fh = io.StringIO()
        stderr_fh = io.StringIO()
        with redirect_stderr(stderr_fh):
            with redirect_stdout(stdout_fh):
                subprocess.run(command, shell=shell)
        error_msg = stderr_fh.getvalue()
        error_msg = error_msg.replace("stdin: is not a tty", "")
        error_msg = error_msg.strip()
        if error_msg:
            raise Exception(error_msg)
        return stdout_fh.getvalue()

    s = lib.servers.get(server)
    s_user = s["ssh-username"]
    s_host = s["host"]
    s_passwd = s["ssh-password"]

    if os.name == "nt":
        if command:
            cmd = 'plink -ssh {s_user}@{s_host} -pw {s_passwd} "{command}"'.format(**locals())
        else:
            cmd = 'putty -ssh {s_user}@{s_host} -pw {s_passwd} "{command}"'.format(**locals())

        ssh_config = Path("~") / ".ssh" / "config"
        ssh_config = ssh_config.expanduser()
        if ssh_config.is_file() and server in ssh_config.read_text():

            #check if we have to use putty or if we already have ssh keys configured
            #Putty opens up in a new window which is annoying, so if ssh keys are already installed we use those,
            #otherwise, we use putty so that we can pass in the password on the command line
            cmd2 = "ssh -q -o ConnectTimeout=1 {server} exit".format(**locals())
            try:
                subprocess.check_output(cmd2) #this will fail if ssh keys are not setup
                cmd = 'ssh {server} "{command}"'.format(**locals())
            except subprocess.CalledProcessError:
                pass
    else:
        cmd = 'sshpass -p{s_passwd} ssh {s_user}@{s_host} "{command}"'.format(**locals())

    try:
        try:
            if vars.verbose:
                print("executing:", cmd)
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            #if putty is not installed, run the normal ssh command and the user will have to type in the password on the command line
            cmd = 'ssh {s_user}@{s_host} "{command}"'.format(**locals())
            if vars.verbose:
                print("nevermind, that command failed. Executing", cmd)
            print("use the password {s_passwd} when prompted".format(**locals()))

            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    except subprocess.CalledProcessError:
        if proc.stderr:
            ssh_error_msg = b"\n".join(proc.stderr.readlines()).decode("utf-8")
            ssh_error_msg = ssh_error_msg.replace("stdin: is not a tty", "")
            ssh_error_msg = ssh_error_msg.strip()
            if ssh_error_msg:
                print()
                print("-"*79)
                print("recieved an error when running the command")
                print(cmd)
                print("-"*79)
                print()
                raise Exception(ssh_error_msg)
        raise

    if proc.stderr:
        ssh_error_msg = b"\n".join(proc.stderr.readlines()).decode("utf-8")
        ssh_error_msg = ssh_error_msg.replace("stdin: is not a tty", "")
        ssh_error_msg = ssh_error_msg.strip()
        if ssh_error_msg:
            print()
            print("-"*79)
            print("recieved an error when running the command")
            print(cmd)
            print("-"*79)
            print()
            raise Exception(ssh_error_msg)

    return b"".join(proc.stdout.readlines()).decode("utf-8")
