import xmlrpc.client
from lib.errors import SmashException
from lib import lastpass
import configparser
from runner import vars

servers = vars.servers

def interactively_add_conf_entry(name):
    if not name:
        name = input("what would you like to name this webfaction entry: ")

    host = input("Enter the host for {}: ".format(name))
    ftp_user = input("Enter the FTP username for {}: ".format(name))
    ftp_password = input("Enter the FTP password for {}: ".format(name))
    same = input("Are the SSH credentials also {} & {} [yes/No]: ".format(ftp_user, ftp_password))
    if same.lower().startswith("y"):
        ssh_user = ftp_user
        ssh_password = ftp_password
    else:
        ssh_user = input("Enter the SSH username for {}: ".format(name))
        ssh_password = input("Enter the SSH password for {}: ".format(name))

    add_conf_entry2(name, host, ftp_user, ftp_password, ssh_user, ssh_password)

    return name

def maybe_add_server_entry(entry):
    if entry in vars.servers:
        return
    interactively_add_conf_entry(entry)


def add_conf_entry(name, lastpass_ftp_name=None, lastpass_ssh_name=None, ssh_is_ftp=False):
    """adds a new credentials to the webfaction conf file
    name is the name by which these webfaction credentials are stored under in the conf file
    a search is also done using this name and is narrowed down by the keyword ftp or ssh
    unless lastpass_ftp_name or lastpass_ssh_name is provided in which case the lastpass
    title must exactly match lastpass_ftp_name or lastpass_ssh_name
    ssh_is_ftp can be set to True if the ftp and ssh credentials are the same"""

    if lastpass_ftp_name:
        lastpass_ftp_account = lastpass.find_exact(lastpass_ftp_name)
        if lastpass_ftp_account is None:
            raise SmashException("could not find a lastpass account with the title {}".format(lastpass_ftp_name))
    else:
        res = list(lastpass.find(name, "ftp"))
        lastpass_ftp_account = res[0]
        if (len(res) > 1):
            raise SmashException('found multiple possible entries in lastpass for "{}" with "{}" in the title. You\'ll need to Pass in the exact lastpass ftp and ssh names to this function.'.format(name, "ftp"))


    if lastpass_ssh_name:
        lastpass_ssh_account = lastpass.find_exact(lastpass_ssh_name)
        if lastpass_ssh_account is None:
            raise SmashException("could not find a lastpass account with the title {}".format(lastpass_ssh_name))
    elif ssh_is_ftp:
        lastpass_ssh_account = lastpass_ftp_account
    else:
        res = list(lastpass.find(name, "ssh"))
        lastpass_ftp_account = res[0]
        if (len(res) > 1):
            raise SmashException('found multiple possible entries in lastpass for "{}" with "{}" in the title. You\'ll need to Pass in the exact lastpass ftp and ssh names to this function.'.format(name, "ftp"))


    ftp_user = lastpass_ftp_account.username.decode()
    ftp_password = lastpass_ftp_account.password.decode()
    ssh_user = lastpass_ssh_account.username.decode()
    ssh_password = lastpass_ssh_account.password.decode()
    host = lastpass_ftp_account.url.decode().lstrip("http://")

    add_conf_entry2(name, host, ftp_user, ftp_password, ssh_user, ssh_password)

def add_conf_entry2(name, host, ftp_user, ftp_password, ssh_user, ssh_password):
    """permamently saves the info passed in a conf file where it can be retrieved from the dictionary vars.webfaction using the name as the dictionary key"""

    conf = vars.webfaction_conf

    try:
        conf.add_section(name)
    except configparser.DuplicateSectionError:
        pass

    conf.set(name, "host", host)
    conf.set(name, "ftp-username", ftp_user)
    conf.set(name, "ftp-password", ftp_password)
    conf.set(name, "ssh-username", ssh_user)
    conf.set(name, "ssh-password", ssh_password)

    with vars.webfaction_conf_loc.open('w') as configfile:
        conf.write(configfile)

    #refresh the vars.webfaction dictionary
    vars.save_webfaction_conf_entries()