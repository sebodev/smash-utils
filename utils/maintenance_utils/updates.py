from lib import wp_cli
from runner import smash_vars
import datetime

#remove these once I don't have to prompt for the google drive folder
import os
from pathlib import Path
from lib import webfaction
from lib import domains
import lib.password_creator
from lib import errors

def main(server, app, save_results=None):
    """Updates all plugins needing updates for a specific website.
    If save_results is True the results are saved to a csv file.
    If False, results are not saved.
    If None, the user is prompted if they would like to save the results"""

    dry_run = wp_cli.run(server, app, "plugin update --all --dry-run --format=summary")

    print("It'll be just a few minutes. I'm going to update the following plugins for you.\n\n"+dry_run+"\n")
    try:
        results = wp_cli.run(server, app, "plugin update --all --format=csv")
    except errors.SSHError as err:
        print(err.message)

    if save_results is False:
        return
    if save_results is True or not input("Would you like to save the plugins being updated [Yes/no]").lower().startswith("n"):
        domain = webfaction.get_domains(server, app)[0]
        update_dir = choose_drive_folder(domain)
        drive_file = update_dir / datetime.datetime.now().strftime("%b %d, %Y - %H%M.csv")
        drive_file.write_text(results)
        if smash_vars.verbose:
            print("wrote results to {}".format(drive_file))


def choose_drive_folder(domain):
    """
    Prompts the user for the Google drive directory to save the data in, and then creates and returns a subdirectory for the monthly data
    Skips prompting the user if there is already a folder that matches the domain name without the .com or .org"""
    d = smash_vars.google_drive_maintenance_dir / "clients"
    assert d.is_dir(), "directory {} does not exist".format(d)
    d_dirs = next(os.walk(str(d)))[1]
    domain_name = domain.replace(".com", "").replace(".org", "")
    if domain_name in d_dirs:
        resp = domain_name
    else:
        print()
        print("Google drive folders: ")
        print(", ".join( d_dirs ))
        print()
        resp = input("which of the above folders would you like me to save the monthly data in: ")
    assert resp in d_dirs
    drive_dir = d / Path(resp) / "Updates"
    if not drive_dir.is_dir():
        drive_dir.mkdir()
    return drive_dir
