import xmlrpc.client
import configparser

from lib.errors import SmashException
from lib import lastpass
from lib import webfaction
from runner import vars
from lib import passwords

def get(server, lookup=None):
    """ returns a dictionary of info about a server entry,
    or lookup a specific item in this dictionary if lookup is specified """
    if lookup:
        return vars.servers[server][lookup]
    return vars.servers[server]

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

    same = input("Are the SSH credentials also {} and {} [Yes/no]: ".format(ftp_user, ftp_password))
    if not same.lower().startswith("n"):
        ssh_user = ftp_user
        ssh_password = ftp_password
    else:
        ssh_user = input("Enter the SSH username for {}: ".format(name))
        ssh_password = input("Enter the SSH password for {}: ".format(name))

    webfaction_user = webfaction_password = None
    resp = input("Is this a Webfaction Server [Yes/no]: ")
    is_webfaction = not bool(resp.startswith("n"))
    if is_webfaction:
        same = input("Are the Webfaction account credentials also {} and {} [Yes/no]: ".format(ssh_user, ssh_password))
        if not same.lower().startswith("n"):
            webfaction_user = ssh_user
            webfaction_password = ssh_password
        else:
            webfaction_user = input("Enter the Webfaction username for {}: ".format(name))
            webfaction_password = input("Enter the Webfaction password for {}: ".format(name))

        add_conf_entry2(name, host, ftp_user, ftp_password, ssh_user, ssh_password, webfaction_user, webfaction_password, is_webfaction)

    return name


def add_conf_entry(name, lastpass_ftp_query=None, lastpass_ssh_query=None, lastpass_webfaction_query=None, ssh_is_ftp=False, webfaction_is_ssh=True):
    """adds a new credentials to the webfaction conf file
    name is the name by which these webfaction credentials are stored under in the conf file
    a search is also done using this name and is narrowed down by the keyword ftp or ssh
    unless lastpass_ftp_query or lastpass_ssh_query or lastpass_webfaction_query is provided in which case the lastpass
    title must exactly match lastpass_ftp_query or lastpass_ssh_query or lastpass_webfaction_query
    ssh_is_ftp can be set to True if the ftp and ssh credentials are the same
    same with webfaction_is_ssh"""

    if lastpass_ftp_query:
        ftp_cred = passwords.lastpass(lastpass_ftp_query, exact_match=True)[0]
    else:
        res = passwords.lastpass(name, "ftp")
        ftp_cred = res[0]
        if (len(res) > 1):
            raise SmashException('found multiple possible entries in lastpass for "{}" with "{}" in the title. You\'ll need to Pass in the exact lastpass ftp and ssh names to this function.'.format(name, "ftp"))


    if lastpass_ssh_query:
        ssh_cred = passwords.lastpass(lastpass_ssh_query, exact_match=True)[0]
    elif ssh_is_ftp:
        ssh_cred = ftp_cred
    else:
        res = passwords.lastpass(name, "ssh")
        ssh_cred = res[0]
        if (len(res) > 1):
            raise SmashException('found multiple possible entries in lastpass for "{}" with "{}" in the title. You\'ll need to Pass in the exact lastpass ftp and ssh names to this function.'.format(name, "ssh"))

    is_webfaction=True
    if lastpass_webfaction_query:
        webfaction_cred = passwords.lastpass(lastpass_webfaction_query, exact_match=True)[0]
    elif webfaction_is_ssh:
        webfaction_cred = ssh_cred
        is_webfaction=webfaction.can_login(ssh_cred.username, ssh_cred.password)
    else:
        res = passwords.lastpass(name, "webfaction")
        webfaction_cred = res[0]
        if (len(res) > 1):
            raise SmashException('found multiple possible entries in lastpass for "{}" with "{}" in the title. You\'ll need to Pass in the exact lastpass entry for the webfaction account.'.format(name, "webfaction"))

    host = ftp_cred.host.lstrip("http://")

    add_conf_entry2(name, host, ftp_cred.username, ftp_cred.password, ssh_cred.username, ssh_cred.password, webfaction_cred.username, webfaction_cred.password, is_webfaction)

def add_conf_entry2(name, host, ftp_user, ftp_password, ssh_user, ssh_password, webfaction_user=None, webfaction_password=None, is_webfaction=False):
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
    conf.set(name, "is-webfaction-server", is_webfaction)
    conf.set(name, "webfaction-username", webfaction_user or "")
    conf.set(name, "webfaction-password", webfaction_password or "")

    with vars.servers_conf_loc.open('w') as configfile:
        conf.write(configfile)

    #refresh the vars.servers dictionary
    save_conf_entries()

#A custom dictionary class is used for the servers dictionary that will add a new entry,
#prompting the user for the necessary info,
#instead of raising a KeyError
class ServersDict(dict):
    def __missing__(self, name):
        if not (input("Would you like to add a new server entry for %s [Yes/no]" % name).lower().startswith("n")):
            interactively_add_conf_entry(name)
            return dict(vars.servers_conf.items(name))
        else:
            raise KeyError("couldn't find the server entry '{}'".format(name))

    def exists(self, server_entry):
        return bool(self.__getitem__(server_entry))

def save_conf_entries():
    """Read whatever is currently in the servers.txt file and saves the result in the vars.servers dictionary"""
    servers = ServersDict()
    for section in vars.servers_conf.sections():
        servers[section] = {}
        for (key, val) in vars.servers_conf.items(section):
            servers[section][key] = val
    vars.servers = servers
