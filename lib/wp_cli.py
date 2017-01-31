from contextlib import redirect_stdout, redirect_stderr
import io, sys, subprocess, os.path

from runner import vars
import lib.errors
from lib import ssh
from lib import webfaction
from lib import servers

def run(server, app, cmd):
    """runs a wp_cli command installing wp_cli if it is not installed """

    wf, wf_id = webfaction.connect(server)
    cmd2 = "test -e " + _root_dir(server, app)+"/wp-cli.phar" + " && echo Exists"
    wp_cli_exists = wf.system(wf_id, cmd2).strip()

    if wp_cli_exists:
        return run2(server, app, cmd)
    else:
        install(server, app)
        return run2(server, app, cmd)

def run2(server, app, cmd):
    """runs a wp_cli command raising subprocess.CalledProcessError if wp_cli is not installed """
    if cmd.startswith("wp "):
        cmd = cmd[len("wp "):]
    cmd.lstrip()
    root = _root_dir(server, app)

    #run with php55 on webfaction servers and with php on all other servers.
    #I believe it was version 5.2+ that is needed to be able to properly run phar files
    if servers.get(server, "is-webfaction-server"):
        cmd = "cd {root} && php55 {root}/wp-cli.phar {cmd}".format(**locals())
    else:
        cmd = "cd {root} && php {root}/wp-cli.phar {cmd}".format(**locals())

    return ssh.run2(server, cmd)

def install(server, app):
    ssh.run(server, "curl -o {}/wp-cli.phar https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar".format(_root_dir(server, app)))

def _root_dir(server, app=None):
    if app:
        return webfaction.get_app_dir(server, app)
    else:
        if servers.get(server, "is-webfaction-server"):
            print()
            print(", ".join(webfaction.get_webapps(server)))
            print()
            while not app:
                app = input("which of the above apps is this for: ")
            return webfaction.get_app_dir(server, app)
        else:
            return input("Enter the full path where WordPress is installed on the server: ")
