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
import lib.lastpass
import lib.webfaction
import sys

def setup_webfaction_conf():
    lib.webfaction.add_conf_entry("sebodev", "Sebodev FTP", "Sebodev SSH")
    lib.webfaction.add_conf_entry("wpwarranty", ssh_is_ftp=True)

def save_personal_info():
    name_guess = getpass.getuser()
    name = input("Is your name {}: [Yes/no]".format(name_guess))
    if name.lower().startswith("n"):
        name = input("What is your name: ")
    else:
        name = name_guess

    email_guess = name.lower() + "@sebodev.com"
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
        project_dir = input("Type in the name of the folder you would like us to download wordpress themes into so you can work  your mad developer skills on them: ")
    google_drive_dir = input("Where is your Google Drive folder. Leave blank if Google Drive was never installed on the computer, but some things won't work: ")
    vars.sebo_conf.set("locations", "project_dir", project_dir)
    if google_drive_dir:
        vars.sebo_conf.set("locations", "google_drive", google_drive_dir)

    assert(os.path.exists(project_dir))
    if google_drive_dir:
        assert(os.path.exists(google_drive_dir))

    vars.sebo_conf.set("locations", "stored_data", vars.storage_dir)
    try:

    except:
    vars.sebo_conf.set("setup_info", "setup_run", "True")

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

    subprocess.run("pip install requests", shell=True)
    subprocess.run("pip install requests --upgrade", shell=True)
    subprocess.run("pip install lxml", shell=True)
    subprocess.run("pip install lxml --upgrade", shell=True)


def main():
    assert sys.version_info >= (3,5), "Big fat mean me says you have to be running Python 3.5+"
    if vars.installed:
        print("welcome back to the installer. What would you like to reconfigure?")
        print()
        print("type 'dependencies' to install the dependencies")
        print("type 'config' to change the config files")
        print()
        the_input = input(": ").strip("'").lower()

        check_path()
        if the_input.startswith("d"):
            install_dependencies()
        if the_input.startswith("c"):
            save_personal_info()
            setup_webfaction_conf()
            save_locations()
    else:
        print("Hola! Let's get things started")
        print("First off, let's go through some yes/no questions\n")
        save_personal_info()
        setup_webfaction_conf()
        print("\nNow we need a couple of locations on your computer")
        save_locations()
        check_path()
        print("\nThanks for the info. Now We just have to install the dependencies")
        install_dependencies()
