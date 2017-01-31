import xmlrpc.client
import configparser

from runner import vars
import lib.errors
from lib import dns
from lib import domains
from lib import servers

#current_account will be a dictionary containing extra info about the last account connected to with the connect() function
current_account = None
xmlrpc_cache = {}
account_cache = {}

def connect(server, version=1):
    global current_account, xmlrpc_cache

    if server in xmlrpc_cache:
        current_account = account_cache[server]
        return xmlrpc_cache[server]

    username = vars.servers[server]["ssh-username"]
    password = vars.servers[server]["ssh-password"]
    if "webfaction-username" in vars.servers[server].keys():
        username = vars.servers[server]["webfaction-username"]
    if "webfaction-password" in vars.servers[server].keys():
        password = vars.servers[server]["webfaction-password"]

    webfaction, wf_id = connect2(username, password, version)

    #xmlrpc_cache[server] = webfaction, wf_id #Caching the connections will sometimes cause problems.
    account_cache[server] = current_account

    return webfaction, wf_id

def connect2(username, password, version=1):
    global current_account

    if vars.verbose:
        print("logging into webfaction with the credentials {} and {}".format(username, password))

    try:
        webfaction = xmlrpc.client.ServerProxy("https://api.webfaction.com/")
        wf_id, current_account = webfaction.login(username, password, "", version)
    except xmlrpc.client.Fault as err:
        if str(err) == "<Fault 1: 'LoginError'>":
            raise lib.errors.LoginError("Failed to login to Webfaction with the credentials {} and {}".format(username, password))
        else:
            raise

    return webfaction, wf_id

def get_webapps(server, domain=None):
    if not domain:
        wf, wf_id = connect(server)
        apps = wf.list_apps(wf_id)
        return [app["name"] for app in apps]
    else:
        ret = []
        wf, wf_id = connect(server)
        resp = wf.list_websites(wf_id)
        for group in resp:
            if domain in group["subdomains"]:
                apps = group["website_apps"]
                ret.extend([app[0] for app in apps])
        ret = list(set(ret)) #remove duplicate entries
        return ret

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
            if group["website_apps"] and app in group["website_apps"][0]:
                return group["subdomains"]

def get_server(domain):
    """gets the server associated with the domain.
    First try checking against a local cache,
    and then try logging into all of the webfaction servers you've told smash-utils the credentials for.
    Each time we login to a website we update the local cache.
    Webfaction accounts with incorrect login info are ignored """

    #method1
    for server_name, server in vars.servers.items():
        ds = server.get("domains")
        if ds:
            for d in ds:
                if d == domain:
                    return server_name

    #method2
    if vars.verbose:
        print("checking all of the Webfaction servers for the domain {}".format(domain))
    for server in vars.servers.keys():
        if servers.get(server, "is-webfaction-server"):
            try:
                domains = get_domains(server)
                vars.servers[server]["domains"] = domains #this is so we will be able to update the cached server entries
                if domain in domains:
                    servers.push_server_entries() #update the cached server entries
                    return server
            except lib.errors.LoginError:
                pass
    servers.push_server_entries()

def get_website(server, domain):
    """returns a list of Webfaction names associated with a domain
    Webfaction allows two domains to be associated with a website if one of them is the https version"""
    ret = []
    wf, wf_id = connect(server)
    sites = wf.list_websites(wf_id)
    for site in sites:
        if domain in site["subdomains"]:
            ret.append(site["name"])
    return ret

def get_app_dir(server, app):
    return "/home/{}/webapps/{}".format(get_user(server), app)

def get_user(server):
    """grabs the name of the webfaction user"""
    if server not in account_cache:
        connect(server)
    return account_cache[server]["username"]

def get_webserver(server):
    """The web server name (something like web535.webfaction.com)"""
    if server not in account_cache:
        connect(server)
    return account_cache[server]["web_server"].lower() + ".webfaction.com"

def get_webserver2(username, password):
    """The web server name (something like web535.webfaction.com)"""
    connect2(username, password)
    return current_account["web_server"].lower() + ".webfaction.com"

def can_login(server):
    if server not in vars.servers:
        return False
    try:
        connect(server)
    except lib.errors.LoginError:
        return False
    return True

def is_webfaction(domain_or_server):
    """ Does it's best to determine if a domain or server is running on a Webfaction server """
    return is_webfaction_server(domain_or_server) or is_webfaction_domain(domain_or_server)

def is_webfaction_server(server):
    """Checks if a server is a Webfaction server. The credentials do not have to be valid, except in a few cases such as when cloudflare is used as a CDN"""
    host = servers.get(server, "host", create_if_needed=False)
    if host:
        if "webfaction" in host:
            return True

        #this takes care of the situation where an ip address was used as the host
        host = dns.get_web_host(host)
        if "webfaction" in host:
            return True

    #take care of the situation where cloudflare is used. The credentials have to be valid
    if can_login(server):
        return True

    return False

def is_webfaction_domain(domain, better_checking=True):
    """ Does a reverse nslookup to check if a domain belongs to Webfaction.
    Reverse nslookups can fail as is the case when a website is on cloudflare.
    If better_checking is True, logs into all servers to try to find the domain if the reverse nslookup failed"""
    host = dns.get_web_host(domain)
    if host and "webfaction" in host:
        return True
    if better_checking:
        return bool(get_server(domain))
    return False
