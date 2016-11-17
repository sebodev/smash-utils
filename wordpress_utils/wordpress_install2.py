'''Creates a new wordpress site on a webfaction server
'''

import os, sys, time, re, socket
import urllib.request, urllib.parse, urllib.error, urllib.parse, unittest
import xmlrpc.client

from runner import vars
from lib import servers
from lib import webfaction
from lib import password_creator
from lib.errors import SmashException
from lib import domains
from lib import passwords

CURRENT_WORDPRESS_VERSION = "wordpress_461"

#app_type can also be static_php70
def create(website, server="sebodev", app_type=CURRENT_WORDPRESS_VERSION):

    while not website:
        website = input("Enter the site name (example cdc.sebodev.com): ")

    if "sebodev.com" in website:
        server = "sebodev"
    if "sitesmash.com" in website:
        server = "sitesmash"
    if not server:
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
        db_name, _, db_user, _ = passwords.db(server, app_name)
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
        #db_password = lib.password_creator.create(8)
        #print(wf.create_db(wf_id, app_name, "mysql", db_password))
        return



    ###############################################
    ## now on to fixing up our wordpres settings ##
    ###############################################

    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import Select
    from selenium.common.exceptions import NoSuchElementException
    from selenium.common.exceptions import NoAlertPresentException
    from selenium.webdriver.common.action_chains import ActionChains

    wp_initial_passwd = wp_password


    if True:
        print('waiting 5 minutes for the site to be created...')
        time.sleep(300)
    if False:
        input('To continue. Push enter once the site is up...')

    try:
        driver = webdriver.Chrome()
        driver.implicitly_wait(30)

        driver.get('http://' + site + "/wp-admin")
        print('let me take a moment to make a few tweaks to your wordpress installation for you...')
        driver.find_element_by_id("user_login").clear()
        driver.find_element_by_id("user_login").send_keys("sebodev")
        driver.find_element_by_id("user_pass").clear()
        driver.find_element_by_id("user_pass").send_keys(wp_initial_passwd)
        driver.find_element_by_id("wp-submit").click()
        driver.get('http://%s.sebodev.com/wp-admin/user-new.php' % site_name)

        #create the sitekeeper user
        def create_password():
            import string, random
            chars = string.ascii_letters + string.digits + string.punctuation
            passwd_size = 16
            password = ''.join((random.SystemRandom().choice(chars)) for i in range(passwd_size))
            print("\nThe wordpress credential are now:")
            print("Login Url: http://" + site + "/wp-admin")
            print("Username: sitekeeper")
            print("Password: " + password)
            return password
        driver.find_element_by_id("user_login").clear()
        driver.find_element_by_id("user_login").send_keys("sitekeeper")
        driver.find_element_by_id("email").clear()
        driver.find_element_by_id("email").send_keys("hi@sebodev.com")
        driver.find_element_by_id("first_name").clear()
        driver.find_element_by_id("first_name").send_keys("Snap")
        driver.find_element_by_id("last_name").clear()
        driver.find_element_by_id("last_name").send_keys("Site")
        driver.find_element_by_id("url").clear()
        driver.find_element_by_id("url").send_keys("http://sebodev.com")
        driver.find_element_by_class_name('wp-generate-pw').click()
        password = create_password()
        time.sleep(.5)
        driver.find_element_by_id('pass1-text').click()
        driver.find_element_by_id('pass1-text').clear()
        driver.find_element_by_id('pass1-text').send_keys(password)
        driver.find_element_by_id("send_user_notification").click()
        Select(driver.find_element_by_id("role")).select_by_visible_text("Administrator")
        driver.find_element_by_id("createuser").click()
        driver.find_element_by_id("createusersub").click()
        driver.get('http://' + site + "/wp-login.php?action=logout")
        driver.find_element_by_link_text("log out").click()


        #log back in and delete the sebodev user
        #
        driver.find_element_by_id("user_login").clear()
        driver.find_element_by_id("user_login").send_keys("sitekeeper")
        driver.find_element_by_id("user_pass").clear()
        driver.find_element_by_id("user_pass").send_keys(password)
        driver.find_element_by_id("wp-submit").click()

        if True:
            driver.get('http://' + site + "/wp-admin/users.php")
            delete = driver.find_element_by_link_text("sebodev")
            ActionChains(driver).move_to_element(delete).move_to_element(
                driver.find_element_by_class_name("submitdelete")
                ).click().perform()

            driver.find_element_by_id("delete_option1").click()
            driver.find_element_by_id("submit").click()

        #change the permalink structure
        driver.get('http://' + site + "/wp-admin/options-permalink.php")
        driver.find_element_by_id("permalink_structure").clear()
        driver.find_element_by_id("permalink_structure").send_keys("/%category%/%postname%/")
        driver.find_element_by_id("submit").click()

        #change the blog name
        driver.get('http://' + site + "/wp-admin/options-general.php")
        driver.find_element_by_id("blogname").clear()
        driver.find_element_by_id("blogname").send_keys(site_name)
        driver.find_element_by_id("blogdescription").clear()
        driver.find_element_by_id("blogdescription").send_keys("")
        driver.find_element_by_id("admin_email").clear()
        driver.find_element_by_id("admin_email").send_keys("hi@sebodev.com")

        #discourage search engine crawls
        driver.get('http://' + site + "/wp-admin/options-reading.php")
        driver.find_element_by_id("blog_public").click()

        driver.find_element_by_id("submit").click()

        driver.quit()
        print('\nAll done. You know have a fancy schnazzy site to play around with.\n')

    except KeyboardInterrupt:
        driver.quit()
        raise
