import socket, xmlrpc

from runner import vars
from lib import domains
from lib import webfaction
from lib import passwords

def main(website):

    if not website:
        resp = input("What would you like to delete?\n"
                      "Enter a to delete an app\n"
                      "Enter d to delete a domain\n"
                      "Enter w to delete a website entry\n"
                      "Enter db to delete a database\n"
                      "Enter db-u to delete a database user\n"
                      "Or type a website to completely delete everything associated with it: "
                     )

        resp = resp.lower()
        server = input("Which server is this for: ")
        wf, wf_id = webfaction.connect(server)

        if resp == "a":
            print("Current apps are: ", ", ".join(webfaction.get_webapps(server)))
            app = input("Enter an app to delete: ")
            wf.delete_app(wf_id, app)
        elif resp == "d":
            domain = input("Enter a domain to delete: ")
            wf.delete_domain(wf_id, domain)
        elif resp == "w":
            site_name = input("Enter a Webfaction website name to delete: ")
            wf.delete_website(wf_id, site_name, ip)
        elif resp == "db":
            db = input("Enter a database to delete: ")
            wf.delete_db(wf_id, db, "mysql")

            r = input("would you like to delete a database user as well [Yes/no]: ")
            if not r.lower().startswith("n"):
                db_user = input("Enter a database user to delete: ")
                wf.delete_db_user(wf_id, db_user, "mysql")
        elif resp == "db-u":
            db_user = input("Enter a database user to delete: ")
            wf.delete_db_user(wf_id, db_user, "mysql")

            r = input("would you like to delete a database as well [Yes/no]: ")
            if not r.lower().startswith("n"):
                db = input("Enter a database user to delete: ")
                wf.delete_db(wf_id, db, "mysql")
        else:
            if not resp:
                print("Well that ruins my fun. Come back when you have something for me to destroy.")
            else:
                website = resp

    if website:

        domain = domains.normalize_domain(website)

        server_info, server, app = domains.info(domain)
        assert(server)

        site_name = webfaction.get_website(server, domain)
        if site_name:
            site_name = site_name[0] #there could also be a second https version of the domain. I'm just ignoring that fact for now
        else:
            site_name = None

        if server and app:
            db, _, db_user, _ = passwords.db(server, app)
        else:
            db = input("What is the database you would like to delete. Leave blank to skip this: ")
            db_user = input("What is the database user you would like to delete. Leave blank to skip this: ")

        resp = input(
            "Here's your last chance. I'm about to delete the following \n\n"
            "domain: {domain}\n"
            "website: {site_name}\n"
            "app: {app}\n"
            "database: {db}\n"
            "database user: {db_user}\n\n"
            "Ok to delete the above items [yes/No]: ".format(**locals()))

        if resp.lower().startswith("y"):

            ip = socket.gethostbyname(server_info["host"])
            wf, wf_id = webfaction.connect(server)

            if domain:
                try:
                    wf.delete_domain(wf_id, domain)
                except xmlrpc.client.Fault as err:
                    if domain.count(".") > 1:
                        subdomain = domain[: domain.find(".")]
                        domain = domain[domain.find(".")+1 :]
                        if vars.verbose:
                            print("deleting sudomain {subdomain} on domain {domain}".format(**locals()))
                        wf.delete_domain(wf_id, domain, subdomain)
                    else:
                        raise err
            if site_name:
                wf.delete_website(wf_id, site_name, ip)
            if app:
                wf.delete_app(wf_id, app)
            if db:
                wf.delete_db(wf_id, db, "mysql")
            if db_user:
                wf.delete_db_user(wf_id, db_user, "mysql")

        else:
            print("ok. I'll leave your precious little website alone.")
