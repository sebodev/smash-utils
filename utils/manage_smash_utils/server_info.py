import lib.webfaction
from runner import smash_vars
import lib.servers
import lib.domains

def main(domain_or_server):
    """look up a server or domain and return info about the server entry.
    If a matching server cannot be found prompts the user if they want to add a new one"""

    #if domain_or_server is a server return the server info
    if domain_or_server in smash_vars.servers.keys():
        server = domain_or_server
        print_server_info(server)
        prompt_add_server(server)
        return

    #if it's not return server info for all of the servers
    if domain_or_server is None:
        for server in smash_vars.servers.keys():
            print("\n", server)
            print_server_info(server, print_header=False)
        lib.domains.refresh_domains_cache()
        return

    #domain_or_server must be a domain. Let's find the accompanying server and display the server info

    domain = domain_or_server.replace("http://", "").replace("https://", "").rstrip("/")
    server = lib.webfaction.get_server(domain)

    if not server:
        resp = input("No server entries exist for {}. Would you like to add one now [Yes/no]: ".format(domain))
        if not resp.lower().startswith("n"):
            lib.servers.interactively_add_conf_entry(domain_or_server)

    else:
        print("\n{} is on the server {}".format(domain, server))
        _, app = lib.domains.get_server_app(domain)
        if app:
            print("and is using the app {}".format(app))
        print_server_info(server, print_header=False)
        prompt_add_server(server)

def prompt_add_server(server):
    print()
    return #use the --edit-website command instead
    resp = input("Would you like to add/change the server entry for {} [yes/No]".format(server))
    if resp.startswith("y"):
        lib.servers.interactively_add_conf_entry(server)

def print_server_info(server, print_header=True):
    if print_header:
        print()
        print("Here's what info I was able to find for the server {}".format(server))
        print()
    for k, v in smash_vars.servers[server].items():
        print(k, "=", v)
