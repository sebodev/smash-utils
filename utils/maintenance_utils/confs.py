from pathlib import Path
from runner import smash_vars
from lib import domains

client = None
domain = None

def main(website):
    if website:
        return create_maintenance_conf(website)
    recreate_maintenance_servers_conf(website)


def create_maintenance_conf(website, client=None, level=None):
    return

    global client, domain

    domain = domains.normalize_domain(website)
    client = get_client(domain, client)
    plan = get_plan(level)
    client_dir = get_google_drive_dir()

    recreate_maintenance_servers_conf()

def get_client(client_folder=None):

    if client_folder:
        d = smash_vars.google_drive_maintenance_dir / "clients"
        d_dirs = next(os.walk(str(d)))[1]
        if client_folder in d_dirs:
            return client_folder
        else:
            if smash_vars.verbose:
                print("Could not find the folder {client_folder} at {d}".format(**locals()))

    client_folder = domain.replace(".com", "").replace(".org", "").replace(".edu", "").replace(".net", "").replace(".", "_")
    return client_folder

def get_google_drive_dir():
    return smash_vars.google_drive_maintenance_dir / "clients" / client

def get_plan(level=None):
    plan = None
    level_to_plan = {
        1: "Wordpress Warranty",
        2: "Site Care",
        3: "Site Care +",
        0: "Custom"
    }

    if level:
        try:
            return level_to_plan[level]
        except IndexError:
            if smash_vars.verbose:
                print(level, "is not a valid plan level")

    for k, v in level_to_plan:
        print(k, v)
    print()

    while plan not in level_to_plan:
        level = input("Enter the corresponding number for the above plan {} is on: ".format(client))
        plan = level_to_plan.get(level)

    return plan

def recreate_maintenance_servers_conf():
    raise NotImplementedError
