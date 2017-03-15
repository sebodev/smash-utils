import os, subprocess
from lib import servers
from runner import smash_vars

def copy(server, remote, local):
    cred = servers.get(server)
    if os.name == "nt":
        cmd = 'pscp -pw {cred[password]} -scp {cred[ssh-username]}@{cred[ssh-password]}:{remote} "{local}"'.format(**locals())
        if smash_vars.verbose:
            print("Running command:", cmd)
        subprocess.run(cmd)
    else:
        raise NotADirectoryError

#C:\Users\Russell>pscp -pw xd4ZgNRuH4zoNuKeFEQf -scp curecrete@207.38.86.23:/home/curecrete/webapps/curecrete/wp-content/uploads/backupbuddy_backups/backup-curecreteconnect_com-2017_02_17-10_27am-full-aq82xv18c5.zip "D:/tmp/"
#stdin: is not a tty
