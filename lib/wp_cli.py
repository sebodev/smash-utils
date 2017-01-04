import subprocess

from runner import vars
import lib.errors
from lib import ssh
from lib import webfaction

def run(server, app, cmd):
    """runs a wp_cli command installing wp_cli if it is not installed """
    try:
        run2(server, app, cmd)
    except subprocess.CalledProcessError:
        install(server, app)
        run2(server, app, cmd)

def run2(server, app, cmd):
    """runs a wp_cli command raising subprocess.CalledProcessError if wp_cli is not installed """
    cmd.lstrip("wp")
    root = _root_dir(server, app)
    cmd = "cd {root} && php {root}/wp-cli.phar {cmd}".format(**locals())
    ssh.run(server, cmd)

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
