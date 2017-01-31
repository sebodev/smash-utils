import configparser, os, subprocess, socket
import xmlrpc.client

import lib.errors
from lib.errors import SmashException
from lib import lastpass
from lib import webfaction
from runner import vars
from lib import passwords
from lib import domains

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

    is_webfaction = False
    try:
        if name:
            ftp_user = input("Enter the FTP username for {}: ".format(name))
            ftp_password = input("Enter the FTP password for {}: ".format(name))
        else:
            ftp_user = input("Enter the FTP username: ")
            ftp_password = input("Enter the FTP password: ")
    except (KeyboardInterrupt, SystemExit):
        raise

    if not name:
        try:
            webfaction.connect2(ftp_user, ftp_password)
            name = webfaction.current_account["username"]
            is_webfaction = True
        except:
            #this must not be a webfaction server
            name = input("what would you like to name this server entry: ")
    else:
        try:
            webfaction.connect2(ftp_user, ftp_password)
            is_webfaction = True
        except:
            pass
    if vars.verbose and name in vars.servers:
        print("Warning: {} is already a server entry and will be overwritten.".format(name))

    webfaction_user = webfaction_password = None
    if not is_webfaction:
        resp = input("Is this a Webfaction Server [Yes/no]: ")
        is_webfaction = not bool(resp.startswith("n"))

    if is_webfaction:
        if can_wf_login(ftp_user, ftp_password):
            webfaction_user = ftp_user
            webfaction_password = ftp_password
        else:
            webfaction_user = input("Enter the Webfaction username for {}: ".format(name))
            webfaction_password = input("Enter the Webfaction password for {}: ".format(name))

    if is_webfaction:
        host = webfaction.get_webserver2(webfaction_user, webfaction_password)
    else:
        host = input("Enter the host (example web353.webfaction.com): ")

    if can_ssh_login(host, ftp_user, ftp_password):
        ssh_user = ftp_user
        ssh_password = ftp_password
    else:
        ssh_user = input("Enter the SSH username for {}: ".format(name))
        ssh_password = input("Enter the SSH password for {}: ".format(name))

    if is_webfaction:
        wf, wf_id = webfaction.connect2(webfaction_user, webfaction_password)
        resp = wf.list_domains(wf_id)
        domains = []
        for group in resp:
            domain = group["domain"]
            domains.append(domain)
            for sub in group["subdomains"]:
                domains.append(sub+"."+domain)
    else:
        domains = input("Enter a comma seperated list of the domains on this server: ")
        domains = list(str(domains).split(","))

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
            webfaction.connect2(ssh_cred.username, ssh_cred.password)
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
    pull_server_entries()

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

def pull_server_entries():
    """Read whatever is currently in the servers.txt file and save the results in the vars.servers dictionary"""
    servers = ServersDict()
    for section in vars.servers_conf.sections():
        servers[section] = {}
        for (key, val) in vars.servers_conf.items(section):
            if key == "domains":
                val = eval(str(val))
            elif key == "is-webfaction-server":
                val = bool(eval(str(val)))
            servers[section][key] = val
    vars.servers = servers

def pull_server_entries2():
    """Read whatever is currently in the servers.txt file and save the results in the vars.servers dictionary.
    Updated: also looks through vars.alternate_server_confs"""
    def _pull_entries(server_conf):
        servers = ServersDict()
        for section in servers_conf.sections():
            servers[section] = {}
            for (key, val) in servers_conf.items(section):
                if key == "domains":
                    val = eval(str(val))
                elif key == "is-webfaction-server":
                    val = bool(eval(str(val)))
                servers[section][key] = val

    vars.servers = _pull_entries(vars.servers_conf)
    for conf in vars.alternate_server_confs:
        raise NotImplementedError

def push_server_entries():
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


def can_ftp_login(host, user, password):
    """ returns if we can login to a ftp account with the provided credentials """
    ip = socket.gethostbyname(domains.normalize_domain(host)) ############
    try:
        ftplib.FTP(ip, user, password)
    except (ftplib.error_reply, ftplib.error_temp, ftplib.error_perm):
        return False
    return True

def can_ssh_login(host, user, password):
    """ returns if we can ssh into a server with the credentials provided """
    try:
        if os.name == "nt":
            cmd = 'putty -ssh {}@{} -pw {} echo "hi" '.format(user, host, password)
            if vars.verbose:
                print("executing", cmd)
            subprocess.check_output(cmd)
        else:
            cmd = "sspass -p{} {}@{} echo 'hi'".format(password, user, host)
            subprocess.check_output(cmd)
    except:
        return False
    return True

def can_wf_login(user, password):
    """returns if we can login into the webfaction api with the credentials provided """
    try:
        webfaction.connect2(user, password)
    except lib.errors.LoginError:
        return False
    return True
