import xmlrpc.client
import configparser

from lib.errors import SmashException
from lib import lastpass
import lib.webfaction
from runner import vars
from lib import passwords

def get(server, lookup=None, create_if_needed=True):
    """ returns a dictionary of info about a server entry,
    or lookup a specific item in this dictionary if lookup is specified
    if create_if_needed is False, returns None if the server entry does not exist
    otherwise the user will be prompted to create a new server entry"""
    if server not in vars.servers:
        if create_if_needed:
            interactively_add_conf_entry(server)
        else:
            return
    if lookup:
        return vars.servers[server].get(lookup)
    return vars.servers[server]

def interactively_add_conf_entry(name=None):

    host = input("Enter the host (example web353.webfaction.com): ")
    ftp_user = input("Enter the FTP username: ")
    ftp_password = input("Enter the FTP password: ")

    while not name:
        try:
            lib.webfaction.connect2(ftp_username, ftp_password)
            name = lib.webfaction.current_account["username"]
        except:
            #this must not be for a webfaction server
            name = input("what would you like to name this server entry: ")

    if vars.verbose and name in vars.server:
        print("Warning: {} is already a server entry and will be overwritten.".format(name))

    webfaction_user = webfaction_password = None
    is_webfaction = ("webfaction" in host)
    if not is_webfaction:
        resp = input("Is this a Webfaction Server [Yes/no]: ")
        is_webfaction = not bool(resp.startswith("n"))

    if is_webfaction:
        same = input("Are the Webfaction account and SSH credentials also {} and {} [Yes/no]: ".format(ftp_user, ftp_password))
    else:
        same = input("Are the SSH credentials also {} and {} [Yes/no]: ".format(ftp_user, ftp_password))

    if not same.lower().startswith("n"):
        ssh_user = ftp_user
        ssh_password = ftp_password
    else:
        ssh_user = input("Enter the SSH username for {}: ".format(name))
        ssh_password = input("Enter the SSH password for {}: ".format(name))

    if is_webfaction:
        if not same.lower().startswith("n"):
            webfaction_user = ssh_user
            webfaction_password = ssh_password
        else:
            webfaction_user = input("Enter the Webfaction username for {}: ".format(name))
            webfaction_password = input("Enter the Webfaction password for {}: ".format(name))

        wf, wf_id = lib.webfaction.connect2(webfaction_user, webfaction_password)
        resp = wf.list_domains(wf_id)
        domains = []
        for group in resp:
            domain = group["domain"]
            domains.append(domain)
            for sub in group["subdomains"]:
                domains.append(sub+"."+domain)
    else:
        domains = input("Enter a comma seperated list of the domains on this server: ")
        domains = list(eval(domains))

    add_conf_entry2(name, host, ftp_user, ftp_password, ssh_user, ssh_password, webfaction_user, webfaction_password, is_webfaction, domains)

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

    is_webfaction = True
    if lastpass_webfaction_query:
        webfaction_cred = passwords.lastpass(lastpass_webfaction_query, exact_match=True)[0]
    elif webfaction_is_ssh:
        webfaction_cred = ssh_cred
        try:
            lib.webfaction.connect2(ssh_cred.username, ssh_cred.password)
        except lib.errors.LoginError:
            is_webfaction = False
    else:
        res = passwords.lastpass(name, "webfaction")
        webfaction_cred = res[0]
        if (len(res) > 1):
            raise SmashException('found multiple possible entries in lastpass for "{}" with "{}" in the title. You\'ll need to Pass in the exact lastpass entry for the webfaction account.'.format(name, "webfaction"))

    host = ftp_cred.host.lstrip("http://")

    add_conf_entry2(name, host, ftp_cred.username, ftp_cred.password, ssh_cred.username, ssh_cred.password, webfaction_cred.username, webfaction_cred.password, is_webfaction)

def add_conf_entry2(name, host, ftp_user, ftp_password, ssh_user, ssh_password, webfaction_user=None, webfaction_password=None, is_webfaction=False, domains=[]):
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
    conf.set(name, "domains", domains)

    with vars.servers_conf_loc.open('w') as configfile:
        conf.write(configfile)

    #refresh the vars.servers dictionary
    pull_conf_entries()

#A custom dictionary class is used for the servers dictionary that will add a new entry,
#prompting the user for the necessary info,
#instead of raising a KeyError
class ServersDict(dict):
    def __missing__(self, name):
        if not (input("I don't have any info for the server {name}. Would you like to add that info now: [Yes/no]".format(name=name)).lower().startswith("n")):
            interactively_add_conf_entry(name)
            return dict(vars.servers_conf.items(name))
        else:
            raise KeyError("couldn't find the server entry '{}'".format(name))

    def exists(self, server_entry):
        return bool(self.__getitem__(server_entry))

def pull_conf_entries():
    """Read whatever is currently in the servers.txt file and save the results in the vars.servers dictionary"""
    servers = ServersDict()
    for section in vars.servers_conf.sections():
        servers[section] = {}
        for (key, val) in vars.servers_conf.items(section):
            servers[section][key] = val
    vars.servers = servers

def save_servers():
    """ saves whatever is in the vars.servers dictionary to the servers.txt file """
    conf = configparser.ConfigParser()
    for section in vars.servers.keys():
        conf[section] = {}
        for data, v in vars.servers[section].items():
            for (key, val) in vars.servers[section].items():
                conf[section][key] = str(val)

    vars.servers_conf = conf
    with vars.servers_conf_loc.open('w') as configfile:
        conf.write(configfile)
