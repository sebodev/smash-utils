'''Creates a new wordpress site on a webfaction server
'''

import os, sys, time, re, socket
import requests
import urllib.request, urllib.parse, urllib.error, urllib.parse, unittest
import xmlrpc.client

from runner import vars
from lib import servers
from lib import webfaction
from lib import password_creator
from lib.errors import SmashException
from lib import domains
from lib import passwords
from lib import wp_cli
import lib.password_creator

CURRENT_WORDPRESS_VERSION = "wordpress-4.7"

#app_type can also be static_php70
def create(website, server=None, app_type=CURRENT_WORDPRESS_VERSION):

    while not website:
        website = input("Enter the site name (example cdc.sitesmash.com): ")

    if "sebodev.com" in website:
        server = "sebodev"
    if "sitesmash.com" in website:
        server = "sitesmash"
    if not server:
        print(website, "sitesmash.com" in website)
        server = input('Enter the server you would like to use (example sebodev): ')

    if app_type == "static":
        app_type = "static_php70"

    site = website.replace("https://", "").replace("https://", "").replace("www.", "").replace(" ", "").rstrip("/")
    ip = socket.gethostbyname(vars.servers[server]["host"])
    webfaction_user = vars.servers[server]["ssh-username"]
    webfaction_passwd = vars.servers[server]["ssh-password"]

    #make everything up to the first period the app_name. If there is no period, that's an impossible website.
    #We must have been given the subdomain name only, and so we prompt the user to enter the website name
    app_name = site
    end = app_name.find(".")
    if end > 0:
        app_name = app_name[:end]
    else:
        wf, wf_id = webfaction.connect(server)
        user = wf.system(wf_id, 'echo "$USER"')
        site_guess = site + ".{}.com".format(user)

        if (input("Is this WordPress site for "+site_guess+"[yes/No]")).startswith("y"):
            site = site_guess
        else:
            site = input("What is the WordPress site you would like to create: ")

    wf, wf_id = webfaction.connect(server)

    #Note from Webfaction: MySQL database names are limited to 16 characters. Therefore, the WordPress application name
    #must be less than 15 characters minus your username.
    #Also application names are limited to twelve characters
    max_length = max(12, 15-len(webfaction.current_account["username"]))
    site_name = app_name
    app_name = app_name[:max_length]
    https = False
    subdomains = [site, "www."+site]

    current_domains = webfaction.get_domains(server, app_name)
    if current_domains:
        domain_exists = subdomains[0] in webfaction.get_domains(server)
    else:
        domain_exists = None

    if domain_exists:
        if vars.verbose:
            print("The domain already exists.")
    else:
        wf.create_domain(wf_id, subdomains[0], "www")

    if app_name in webfaction.get_webapps(server):
        site_name = webfaction.get_website(server, app_name)
        try:
            db_name, _, db_user, _ = passwords.db(server, app_name)
        except SmashException:
            raise Exception("application {} already exists, and does not appear to have a wordpress installation in it. Unable to proceed. Remove the app with the --delete command, and then re-run this command".format(app_name))
        resp = input("Hmm, The Webfaction app {} already exists. Do you want to delete the website {}, the app {}, and the database {} [yes/No]".format(app_name, site_name, app_name, db_name))
        if resp.lower().startswith("y"):
            #raise SmashException("Webapp already exists")
            if vars.verbose:
                print("deleting website with the name={} and ip address={}".format(site_name, ip))
            try:
                wf.delete_website(wf_id, site_name, ip)
            except xmlrpc.client.Fault:
                #will fail if the site name is different from the app name
                #could be fixed by retrieving the actual site name when we need to delete a website
                #instead of trying to use the app name for the site name
                #but I don't expect we'll be needing to recreate websites that often
                raise SmashException("Failed to delete {}. You'll have to manually delete it".format(site_name))
            wf.delete_app(wf_id, app_name)
            wf.delete_db(wf_id, db_name, "mysql")
            wf.delete_db_user(wf_id, db_user, "mysql")
            time.sleep(1)
            res = wf.create_app(wf_id, app_name, app_type)
        else:
            res = wf.list_apps(wf_id)
            for app in res:
                if app["name"] == app_name:
                    res = app
                    break
            else:
                raise Exception("Failed to retrieve info for the app {}. You'll have to delete the app and try again.".format(app_name))
    else:
        if vars.verbose:
            print("creating app with the name={} and type={}".format(app_name, app_type))
        res = wf.create_app(wf_id, app_name, app_type)

    wp_password = res['extra_info']
    if vars.verbose:
        print("wordpress password: %s" % wp_password)
    if vars.verbose:
        print("creating the website where site_name={}, ip={}, https={}, domains={}, apps={}".format(site_name, ip, https, subdomains, [app_name, "/"]))
    res = wf.create_website(wf_id, site_name, ip, https, subdomains, [app_name, "/"])

    try:
        site_id = res['id']
        assert(site_id)
    except:
        raise Exception("Failed to create the website :( I couldn't find an id for the website and that's all I know")

    if "wordpress" not in app_type:
        if not input("Would you like to create a database[Y/n]").startswith("n"):
            db_password = lib.password_creator.create(8)
            print("created the following database")
            print(wf.create_db(wf_id, app_name, "mysql", db_password))
        return



    ###############################################
    ## now on to fixing up our wordpres settings ##
    ###############################################

    wp_initial_passwd = wp_password
    user = wf.system(wf_id, 'echo "$USER"')

    print("Waiting for the new site to be created", end="")

    def loading_dots():
        while True:
            yield("\rWaiting for the new site to be created.   ")
            yield("\rWaiting for the new site to be created..  ")
            yield("\rWaiting for the new site to be created... ")

    def site_is_up():
        #I'm considering the site ready to be used once we're able to successfully login to the website
        post_data = {
            'proxyUsername': user,
            'proxyPassword': wp_password,
            'proxyRememberUser': True
        }
        return requests.post("http://"+site, data=post_data)

    max_attempts = 50
    dots = loading_dots()
    for i in range(max_attempts):
        if site_is_up():
            break
        time.sleep(3)
        print(next(dots), end="", flush=True)
        sys.stdout.flush()
    else:
        raise Exception(
                            ("I'm bored of waiting for the website to be created.\n"
                            "After waiting for like at least {} seconds, I'm still not able to login.\n"
                            "You'll have to finish configuring the website yourself."
                            ).format(max_attempts*3)
                        )

    print("\nwaiting 30 more seconds to make sure everything finishes copying, and then I'll start configuring things")
    time.sleep(30)

    if vars.verbose:
        print("installing wp-cli, creating the sitekeeper user, and removing the {} user".format(user))
    wp_cli.run(server, app_name, "wp user create sitekeeper hi@sitesmash.com --role=administrator")
    password = password_creator.create(length=14)
    time.sleep(1)
    wp_cli.run(server, app_name, "wp user update sitekeeper --display_name='Site Smash' --user_pass='{}'".format(password))
    print("{} username: sitekeeper new password: {}".format(site, password))
    time.sleep(1)
    wp_cli.run(server, app_name, "wp user delete 1 --reassign=2 ".format())

    if vars.verbose:
        print("updating blog name and permalink structure")
    time.sleep(1)
    wp_cli.run(server, app_name, "wp option update blogname {}".format(site_name))
    time.sleep(1)
    wp_cli.run(server, app_name, "wp rewrite structure '/%category%/%postname%/'")

    if vars.verbose:
        print("configuring installed plugins")

    wp_cli.run(server, app_name, "wp plugin delete hello")
    wp_cli.run(server, app_name, "wp plugin delete jetpack")

    # try:
    #     wp_cli.run(server, app_name, "wp plugin deactivate hello")
    #     wp_cli.run(server, app_name, "wp plugin delete hello")
    # except:
    #     if vars.verbose:
    #         print("failed to remove the hello-dolly plugin. Continuing normally.")
    #
    # try:
    #     wp_cli.run(server, app_name, "wp plugin deactivate jetpack")
    #     wp_cli.run(server, app_name, "wp plugin delete jetpack")
    # except:
    #     if vars.verbose:
    #         print("failed to remove the jetpack plugin. Continuing normally.")

    wp_cli.run(server, app_name, "wp plugin install {} --activate".format("https://downloads.wordpress.org/plugin/wordpress-seo.4.0.2.zip"))
    wp_cli.run(server, app_name, "wp plugin install {}".format("https://downloads.wordpress.org/plugin/advanced-custom-fields.4.4.11.zip"))
    wp_cli.run(server, app_name, "wp plugin install {}".format("https://downloads.wordpress.org/plugin/google-analytics-for-wordpress.5.5.4.zip"))
    wp_cli.run(server, app_name, "wp plugin install {}".format("https://downloads.wordpress.org/plugin/mainwp-child.3.2.7.zip"))

    wp_cli.run(server, app_name, "wp plugin update --all")

    print(
              ("\nAll done. You know have a fancy schnazzy site to play around with.\n "
              "Your credentials are: \n"
              "\n"
              "login URL: {} \n"
              "username: sitekeeper \n"
              "password: {} \n"
              "\n"
              ).format("http://"+site+"/wp-admin", password)
         )
