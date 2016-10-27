import xmlrpc.client
from lib.errors import SmashException
from lib import lastpass
import configparser
from runner import vars
from lib import webfaction

def get(server, lookup):
    return vars.servers[server][lookup]

def interactively_add_conf_entry(name=None):

    host = input("Enter the host (example web353.webfaction.com): ")
    ftp_user = input("Enter the FTP username: ")
    ftp_password = input("Enter the FTP password: ")

    while not name:
        try:
            webfaction = xmlrpc.client.ServerProxy("https://api.webfaction.com/")
            wf_id, current_account = webfaction.login(ftp_username, ftp_password)
            name = webfaction.current_account["username"]
        except:
            #this must not be for a webfaction server
            name = input("what would you like to name this server entry: ")

    if vars.verbose and name in vars.server:
        print("Warning: {} is already a server entry and will be overwritten.".format(name))

    same = input("Are the SSH credentials also {} & {} [yes/No]: ".format(ftp_user, ftp_password))
    if same.lower().startswith("y"):
        ssh_user = ftp_user
        ssh_password = ftp_password
    else:
        ssh_user = input("Enter the SSH username for {}: ".format(name))
        ssh_password = input("Enter the SSH password for {}: ".format(name))

    add_conf_entry2(name, host, ftp_user, ftp_password, ssh_user, ssh_password)

    return name


def add_conf_entry(name, lastpass_ftp_query=None, lastpass_ssh_query=None, ssh_is_ftp=False):
    """adds a new credentials to the webfaction conf file
    name is the name by which these webfaction credentials are stored under in the conf file
    a search is also done using this name and is narrowed down by the keyword ftp or ssh
    unless lastpass_ftp_query or lastpass_ssh_query is provided in which case the lastpass
    title must exactly match lastpass_ftp_query or lastpass_ssh_query
    ssh_is_ftp can be set to True if the ftp and ssh credentials are the same"""

    if lastpass_ftp_query:
        lastpass_ftp_account = lastpass.find_exact(lastpass_ftp_query)
        if lastpass_ftp_account is None:
            raise SmashException("could not find a lastpass account with the title {}".format(lastpass_ftp_query))
    else:
        res = list(lastpass.find(name, "ftp"))
        lastpass_ftp_account = res[0]
        if (len(res) > 1):
            raise SmashException('found multiple possible entries in lastpass for "{}" with "{}" in the title. You\'ll need to Pass in the exact lastpass ftp and ssh names to this function.'.format(name, "ftp"))


    if lastpass_ssh_query:
        lastpass_ssh_account = lastpass.find_exact(lastpass_ssh_query)
        if lastpass_ssh_account is None:
            raise SmashException("could not find a lastpass account with the title {}".format(lastpass_ssh_query))
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
    """permamently saves the info passed in a conf file where it can be retrieved from the dictionary vars.servers using the name as the dictionary key"""

    conf = vars.servers_conf

    try:
        conf.add_section(name)
    except configparser.DuplicateSectionError:
        pass

    conf.set(name, "host", host)
    conf.set(name, "ftp-username", ftp_user)
    conf.set(name, "ftp-password", ftp_password)
    conf.set(name, "ssh-username", ssh_user)
    conf.set(name, "ssh-password", ssh_password)

    with vars.servers_conf_loc.open('w') as configfile:
        conf.write(configfile)

    #refresh the vars.servers dictionary
    save_conf_entries()

def save_conf_entries():
    """Read whatever is currently in the servers.txt file and saves the result in the vars.servers dictionary"""
    servers = {}
    for section in vars.servers_conf.sections():
        servers[section] = {}
        for (key, val) in vars.servers_conf.items(section):
            servers[section][key] = val
    vars.servers = servers
