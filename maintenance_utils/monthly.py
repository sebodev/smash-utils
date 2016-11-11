import os, datetime
from pathlib import Path

from lib import servers
from lib import webfaction
from lib import errors
from lib import passwords
from maintenance_utils import ssl_check
from maintenance_utils import performance_test
from maintenance_utils import security_info
from runner import vars

def main(domain, server):

    while not domain:
        domain = input("Howdy, what website are we looking at today: ")

    if not server:
        server = webfaction.get_server(domain)
    while not server:
        server = input("What server is {} on: ".format(domain))

    domain = domain.replace("http://", "").replace("https://", "").replace("www.", "").rstrip("/")

    if webfaction.can_login(server):
        if domain not in webfaction.get_domains(server):
            raise errors.SmashException("{} isn't on the server {}".format(domain, server))

        apps = webfaction.get_webapps(server, domain)
        if len(apps) == 1:
            app = apps[0]
        else:
            app = input("which of these webfaction webapps would you like me to use {}".format(apps))

    else:
        app = input("Enter the path to the directory WordPress is installed in: ")


    drive_dir = choose_drive_folder(domain)
    security(drive_dir, server, app)
    ssl(drive_dir, domain, server)
    performance(drive_dir, domain)

def choose_drive_folder(domain):
    """
    Prompts the user for the Google drive directory to save the data in, and then creates and returns a subdirectory for the monthly data
    Skips prompting the user if there is already a folder that matches the domain name without the .com or .org"""
    d = vars.google_drive_maintenance_dir / "clients"
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
    assert(resp in d_dirs)
    drive_dir = d / Path(resp) / "Monthly Reports" / datetime.datetime.now().strftime("%B")
    if not drive_dir.is_dir():
        drive_dir.mkdir()
    return drive_dir

def ssl(drive_dir, domain, server):
    print()
    if vars.verbose:
        print("running ssl check...")
    days_left = ssl_check.check_domain(domain)
    if (days_left > 50):
        pass
    else:
        print("!!! WARNING the SSL certificate expires in {} days !!!".format(days_left))
    (drive_dir/"ssl_info.txt").write_text("The SSL certificate expires in {} days.".format(days_left))
    return days_left

def security(drive_dir, server, app):
    print()
    if vars.verbose:
        print("checking security info...")
    db_name, db_host, db_user, db_password = passwords.db(server, app)
    lockouts = security_info.number_of_lockouts(servers.get(server, "ssh-username"), servers.get(server, "host"), db_user, db_password, db_name)
    for k, v in lockouts.items():
        print(k, "=", str(v))
    (drive_dir/"lockout_info.txt").write_text(str(lockouts))
    return lockouts

def performance(drive_dir, domain):
    print()
    if vars.verbose:
        print("running performance test...")
    pagespeed_output_file = drive_dir / "performance_test.csv"
    insights_output_file = drive_dir / "performance_insights.csv"
    performance_test.run(domain, save_file_loc=pagespeed_output_file, insight_sav_loc=insights_output_file)
    return (pagespeed_output_file, insights_output_file)
