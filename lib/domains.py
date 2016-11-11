from runner import vars
from lib import servers
from lib import webfaction
import lib.errors

def normalize_domain(website):
    """ returns the domain for a given website """
    return website.replace("http://", "").replace("https://", "").lstrip("www.").rstrip("/")

def info(domain_or_server, create_if_needed=True):
    """ Returns the tuple server_info, server, app
    If this is not a Webfaction server, server and app will be None
    Otherwise they will be the server name and app name
    server_info will be a dictionary of credentials for the server """
    domain = normalize_domain(domain_or_server)
    server_info = server = app = None
    if webfaction.is_webfaction_domain(domain):
        server = webfaction.get_server(domain)
        if server:
            app = webfaction.get_webapps(server, domain)[0]
        elif webfaction.can_login(domain) and domain in vars.servers:
            server = domain
    if server:
        server_info = servers.get(server)
    elif create_if_needed:
        resp = input("No server entries exists for the domain {}. Would you like to add one now [Yes/no] ".format(domain))
        if not resp.lower().startswith("n"):
            server = servers.interactively_add_conf_entry()
            try:
                app = webfaction.get_webapps(server, domain)[0]
            except:
                pass
        else:
            raise lib.errors.SmashException("Ok. Let me know if you ever do feel like providing info for {}".format(domain))
    return server_info, server, app

def refresh_domains_cache():
    """The domains associated with each server are cached. This function logs into every server and refreshes that cache.
    If no domains can be found for a server (this will happen with any non-webfaction server),
    whatever was previously in the cache will remain in the cache """
    print("\nRefreshing domain info...")
    for server_name, server in vars.servers.items():
        ds = webfaction.get_domains(server_name)
        if ds:
            server["domains"] = ds
    servers.save_servers()
