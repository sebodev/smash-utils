from runner import vars
from lib import servers
from lib import webfaction
import lib.errors

def normalize_domain(website):
    """ returns the domain for a given website """
    return website.replace("http://", "").replace("https://", "").lstrip("www.").rstrip("/")

def get_sever(domain):
    return info(domain)[1]
    """ If this is a Webfaction app, return the name of the server, otherwise returns None """

def get_sever_app(domain):
    """ Returns the tuple (server, app)
    If this is not a Webfaction server, server and app will be None """
    return info(domain)[1:2]

def get_severObj_server_app(domain):
    """ Returns the tuple (server, app)
    If this is not a Webfaction server, server and app will be None """
    return info(domain)

def info(domain_or_server, create_if_needed=True):
    """ Deprecated use get_severObj_server_app(), get_sever_app(), or get_sever()
    Returns the tuple (server_info, server, app)
    If this is not a Webfaction server, server and app will be None
    server_info will be a dictionary of credentials for the server """
    domain = normalize_domain(domain_or_server)
    server_info = server = app = None

    if domain_or_server in vars.servers:
        server = domain_or_server
        try:
            app = webfaction.get_webapps(server, domain)
        except lib.errors.LoginError:
            app = None
        if app:
            app = app[0]
        if vars.verbose:
            print("domain", domain, "maps to the server", server, "and the app", app)
    elif webfaction.is_webfaction_domain(domain):
        server = webfaction.get_server(domain)
        if server:
            try:
                app = webfaction.get_webapps(server, domain)
            except lib.errors.LoginError:
                app = None
            if app:
                app = app[0]
            if vars.verbose:
                print("domain", domain, "maps to the server", server, "and the app", app)
        elif webfaction.can_login(domain) and domain in vars.servers:
            server = domain_or_server
    else:
        for server_name, s in vars.servers.items():
            ds = s.get("domains")
            if ds:
                for d in ds:
                    if d == domain:
                        server = server_name
        if not server: #I don't think thse two lines should be here, but I'm not sure
            server = domain_or_server

    if not server and app: #see if this is a subdomain of a domain we have info about
        parent = parent_domain(server)
        if parent:
            #setting create_if_needed to False. If it was passed in as True, it will still prompt if we would like to create
            #a new server entry as soon as we finish checking the parent domain
            info(parent, create_if_needed=False)


    if server: #this will be True unless we need to create a new server entry
        server_info = servers.get(server)
    elif create_if_needed:
        if "." not in domain:
            raise lib.errors.SmashException("Whoops {} is not a valid website.".format(domain))
        resp = input("No server entries exists for the domain {}. Would you like to add one now [Yes/no] ".format(domain))
        if not resp.lower().startswith("n"):
            server = servers.interactively_add_conf_entry()
            server_info = servers.get(server)
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
        ds = None
        try:
            if server["is-webfaction-server"]:
                ds = webfaction.get_domains(server_name)
        except lib.errors.LoginError as err:
            print()
            print("!!!!! unable to login to {} !!!!!".format(server_name))
            print()
            raise err
        if ds:
            server["domains"] = ds
    servers.push_server_entries()

def parent_domain(subdomain):
    """ return the parent domain of a subdomain or None if no parent domains exist.
    Does not work with TLDs that have multiple periods such as .co.uk """
    if subdomain.count(".") > 1:
        parent = subdomain[subdomain.find(".")+1 :]
        return parent
        #sub = subdomain[: subdomain.find(".")]

def _get_domains_from_subdomain(domain):
    """ Returns all possible domains based off a subdomain.
    Example the string "a.b.c.com" will return ["b.c.com", "c.com"] """
    subdomain = []
    while domain.count(".") > 1:
        subdomain = domain[: domain.find(".")]
        domain = domain[domain.find(".")+1 :]
        subdomains.append(subdomain)
