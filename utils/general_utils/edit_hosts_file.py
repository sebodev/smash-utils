import os
import subprocess
from runner import smash_vars

def main():
    """Opens the hosts file in vi or notepad """
    if os.name == "nt":
        cmd = "{} notepad.exe {}".format(smash_vars.script_dir/"lib"/"elevate64.exe", "C:\Windows\System32\drivers\etc\hosts")
        subprocess.run(cmd)
    else:
        subprocess.run("sudo vi /etc/hosts")
