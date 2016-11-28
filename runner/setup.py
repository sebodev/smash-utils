"""The setup does the following
ask for name
ask for email for connecting to lastpass, drive, etc.
connect to drive and store key for decrypting lastpass password
saves sebodev webfaction login info from lastpass
saves location for projects
saves location on disk of Google drive files
installs dependencies
prompts the user to add this script to the system path if it hasn't been done
keep track if first or repeat time running setup and prompt what to reconfigure second time running script"""

import os, os.path, subprocess, configparser, getpass

from runner import vars
try:
    import lib.lastpass
except ImportError:
    subprocess.run("pip install --upgrade google-api-python-client")
    import lib.lastpass
import lib.webfaction
import sys

def setup_servers_conf():
    lib.servers.add_conf_entry("sebodev", "Sebodev FTP", "Sebodev SSH", "Sebodev Webfaction Account")
    lib.servers.add_conf_entry("sitesmash", "sitesmash webfaction account", "sitesmash webfaction account", "sitesmash webfaction account")
    lib.servers.add_conf_entry("wpwarranty", ssh_is_ftp=True)

def save_personal_info():
    name_guess = getpass.getuser()
    name = input("Is your first name {}: [Yes/no]".format(name_guess))
    if name.lower().startswith("n"):
        name = input("What is your name: ")
    else:
        name = name_guess

    email_guess = name.lower() + "@sitesmash.com"
    email = input("Is your email {}: [Yes/no]".format(email_guess))
    if email.lower().startswith("n"):
        email = input("What is your email: ")
    else:
        email = email_guess

    lastpass_guess = email_guess
    lastpass_email = input("Did you register with lastpass using the email {}: [Yes/no]".format(lastpass_guess))
    if lastpass_email.lower().startswith("n"):
        lastpass_email = input("What email address did you use: ")
    else:
        lastpass_email = email_guess

    print("one moment please...")
    lib.lastpass.save_username(lastpass_email)


def save_locations():
    project_dir = None
    while not project_dir:
        project_dir = input("Type in the name of the folder you would like us to download wordpress themes into so you can work your mad developer skills on them: ")
    google_drive_dir = input("Where is your Google Drive folder. If Google Drive hasn't been installed, you'll want to install it: ")

    if not vars.sebo_conf.has_section('locations'):
        vars.sebo_conf.add_section('locations')
    if not vars.sebo_conf.has_section('setup_info'):
        vars.sebo_conf.add_section('setup_info')

    vars.sebo_conf.set("locations", "project_dir", project_dir)
    if google_drive_dir:
        vars.sebo_conf.set("locations", "google_drive", google_drive_dir)

    assert(os.path.exists(project_dir))
    if google_drive_dir:
        assert(os.path.exists(google_drive_dir), google_drive_dir + " does not exist")

    vars.sebo_conf.set("locations", "stored_data", vars.storage_dir)
    vars.sebo_conf.set("setup_info", "setup_ran", "True")

    try:
        if os.name == "nt":
            version = subprocess.check_output("cd /d {} && cd {} && git rev-parse --verify HEAD".format(vars.script_dir.drive, vars.script_dir), shell=True)
        else:
            version = subprocess.check_output("cd {} && git rev-parse --verify HEAD".format(vars.script_dir.drive, vars.script_dir), shell=True)
        vars.sebo_conf.set("setup_info", "version_setup_run", version.decode("utf-8"))
    except:
        pass

    with vars.sebo_conf_loc.open('w') as configfile:
        vars.sebo_conf.write(configfile)
    vars.save_sebo_conf_vars()

def check_path():
    path = os.environ["PATH"]
    if str(vars.script_dir) not in path:
        input("Add {} to the system path, and then hit enter to continue".format(vars.script_dir))

def install_dependencies():
    input("If not already installed, install nodejs from {} and push enter to continue".format("https://nodejs.org/en/download"))
    input("Gracias. If you don't already have an editor you like to use, install atom from http://atom.io, and I will sync all of your future projects so that they will auto-upload changes you make in atom")

    subprocess.run("npm install -g bower", shell=True)
    subprocess.run("npm install -g gulp", shell=True)
    subprocess.run("npm install -g ruby", shell=True)

    subprocess.run("gem install sass", shell=True)

    subprocess.run("apm install remote-sync", shell=True)

    subprocess.run("pip install --upgrade requests", shell=True)
    try:
        subprocess.check_output("pip install --upgrade lxml", shell=True)
    except subprocess.CalledProcessError:
        input("pip install the appropriate lxml package from {}".format("http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml"))
    subprocess.run("pip install --upgrade pycrypto", shell=True)
    subprocess.run("pip install --upgrade google-api-python-client", shell=True)

def main():
    assert sys.version_info >= (3,5), "Big fat mean me says you have to be running Python 3.5+. You are currently running version {}".format(sys.version_info)
    if vars.installed:
        print("welcome back to the installer. What would you like to reconfigure?")
        print()
        print("type 'dependencies' to install the dependencies")
        print("type 'config' to change the config files")
        print("type 'rerun' to re-run everythin")
        print()
        the_input = input(": ").strip("'").lower()

        check_path()
        if the_input.startswith("d"):
            install_dependencies()
        if the_input.startswith("c"):
            save_personal_info()
            setup_servers_conf()
            save_locations()
        if the_input.startswith("r"):
            save_personal_info()
            setup_servers_conf()
            save_locations()
            install_dependencies()
    else:
        print("Hola! Let's get things started")
        print("First off, let's go through some yes/no questions\n")
        save_personal_info()
        print("\nNow we need a couple of locations on your computer")
        save_locations()
        setup_servers_conf()
        check_path()
        print("\nThanks for the info. Now We just have to install the dependencies")
        install_dependencies()
