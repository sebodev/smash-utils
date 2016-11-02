import xmlrpc.client
import lib.errors
from lib import lastpass
import configparser
from runner import vars

from . import servers

#current_account will be a dictionary containing extra info about the last account connected to with the connect() function
current_account = None
xmlrpc_cache = {}
account_cache = {}

def connect(server):
    global current_account, xmlrpc_cache

    if server in xmlrpc_cache:
        current_account = account_cache[server]
        return xmlrpc_cache[server]

    webfaction = xmlrpc.client.ServerProxy("https://api.webfaction.com/")
    username = vars.servers[server]["ssh-username"]
    password = vars.servers[server]["ssh-password"]
    if "webfaction-username" in vars.servers[server].keys():
        username = vars.servers[server]["webfaction-username"]
    if "webfaction-password" in vars.servers[server].keys():
        password = vars.servers[server]["webfaction-password"]

    if vars.verbose:
        print("logging into webfaction with the credentials {} and {}".format(username, password))

    try:
        wf_id, current_account = webfaction.login(username, password)
    except xmlrpc.client.Fault as err:
        if str(err) == "<Fault 1: 'LoginError'>":
            raise lib.errors.LoginError("Failed to login to Webfaction with the credentials {} and {}".format(username, password))
        else:
            raise

    xmlrpc_cache[server] = webfaction, wf_id
    account_cache[server] = current_account
    return webfaction, wf_id

def get_webapps(server, domain=None):
    if not domain:
        wf, wf_id = connect(server)
        apps = wf.list_apps(wf_id)
        return [app["name"] for app in apps]
    else:
        wf, wf_id = connect(server)
        resp = wf.list_websites(wf_id)
        for group in resp:
            if domain in group["subdomains"]:
                apps = group["website_apps"]
                return [app[0] for app in apps]

def get_domains(server, app=None):
    if not app:
        wf, wf_id = connect(server)
        resp = wf.list_domains(wf_id)
        domains = []
        for group in resp:
            domain = group["domain"]
            domains.append(domain)
            for sub in group["subdomains"]:
                domains.append(sub+"."+domain)
        return domains
    else:
        wf, wf_id = connect(server)
        resp = wf.list_websites(wf_id)
        for group in resp:
            if app in group["website_apps"][0]:
                return group["subdomains"]

def get_server(domain):
    """ Checks every server stored in the servers file to see which server the domain is on """
    for server in vars.servers.keys():
        try:
            if domain in get_domains(server):
                return server
        except lib.errors.LoginError:
            pass

def get_user(server):
    """grabs the name of the webfaction user"""
    return account_cache[server]["username"]

def can_login(server):
    if server not in vars.servers:
        return False
    try:
        connect(server)
    except lib.errors.LoginError:
        return False
    return True
