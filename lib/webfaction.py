import xmlrpc.client
from lib.errors import SmashException
from lib import lastpass
import configparser
from runner import vars

from . import servers

#the xmlrpc object for communicating with webfaction see https://docs.webfaction.com/xmlrpc-api/tutorial.html#getting-started and https://docs.webfaction.com/xmlrpc-api/apiref.html#method-login
#the session id will automatically be provided

def xmlrpc_connect(server):
    webfaction = xmlrpc.client.ServerProxy("https://api.webfaction.com/")
    ftp_username = vars.webfaction[server]["ftp-username"]
    ftp_password = vars.webfaction[server]["ftp-password"]
    wf_id = webfaction.login(ftp_username, ftp_password)[0]
    return webfaction, wf_id

def get_webapps(server):
    wf, wf_id = xmlrpc_connect(server)
    wf.list_apps(wf_id)
    return [app["name"] for app in apps]




#these have been moved to the servers module

def interactively_add_conf_entry(name):
    return servers.interactively_add_conf_entry(name)

def maybe_add_server_entry(entry):
    return servers.maybe_add_server_entry(entry)

def add_conf_entry(name, lastpass_ftp_name=None, lastpass_ssh_name=None, ssh_is_ftp=False):
    return servers.add_conf_entry(name, lastpass_ftp_name, lastpass_ssh_name, ssh_is_ftp)

def add_conf_entry2(name, host, ftp_user, ftp_password, ssh_user, ssh_password):
    return servers.add_conf_entry2(name, host, ftp_user, ftp_password, ssh_user, ssh_password)
