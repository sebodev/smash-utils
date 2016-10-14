import xmlrpc.client
from lib.errors import SmashException
from lib import lastpass
import configparser
from runner import vars

from . import servers

#this will be a dictionary containing extra info about the last account connected to with the connect() function
current_account = None
xmlrpc_cache = {}
current_account_cache = {}

def connect(server):
    global current_account, xmlrpc_cache
    if server in xmlrpc_cache:
        current_account = current_account_cache[server]
        return xmlrpc_cache[server]

    webfaction = xmlrpc.client.ServerProxy("https://api.webfaction.com/")
    ftp_username = vars.webfaction[server]["ssh-username"]
    ftp_password = vars.webfaction[server]["ssh-password"]
    if vars.verbose:
        print("logging into webfaction with the credentials {} and {}".format(ftp_username, ftp_password))
    wf_id, current_account = webfaction.login(ftp_username, ftp_password)

    xmlrpc_cache[server] = webfaction, wf_id
    current_account_cache[server] = current_account
    return webfaction, wf_id

def xmlrpc_connect(server):
    return connect(server)

def get_webapps(server):
    wf, wf_id = xmlrpc_connect(server)
    wf.list_apps(wf_id)
    return [app["name"] for app in apps]




#these have been moved to the servers module

def interactively_add_conf_entry(name):
    return servers.interactively_add_conf_entry(name)

def add_conf_entry(name, lastpass_ftp_name=None, lastpass_ssh_name=None, ssh_is_ftp=False):
    return servers.add_conf_entry(name, lastpass_ftp_name, lastpass_ssh_name, ssh_is_ftp)

def add_conf_entry2(name, host, ftp_user, ftp_password, ssh_user, ssh_password):
    return servers.add_conf_entry2(name, host, ftp_user, ftp_password, ssh_user, ssh_password)
