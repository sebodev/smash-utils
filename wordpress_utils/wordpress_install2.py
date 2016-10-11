'''Creates a new wordpress site on a webfaction server
'''

import os, sys, time, re
import urllib.request, urllib.parse, urllib.error, urllib.parse, unittest

from runner import vars
from lib import servers
from lib import webfaction
from lib import password_creator

def main(website, server=None):
    if not server:
        #server = "sebodev"
        server = "wpwarranty"

    website = website.replace(' ', '')
    app_name = website.replace("http://", "").replace("https://", "")

    webfaction_user = vars.servers[server]["ssh-username"]
    webfaction_passwd = vars.servers[server]["ssh-password"]
    wf, wf_id = webfaction.xmlrpc_connect(server)

    #wf.create_app(wf_id, website, "static_php70")
    sebodev_ip = "75.126.217.39"
    wpwarranty_ip = "75.126.24.91"
    ip = wpwarranty_ip
    app_name = website.replace(".com", "").replace(".org", "")[:12]
    https = False
    app_type = "static_php70"
    app_type = "wordpress_461"
    site = website + ".wpwarranty.webfactional.com"
    subdomains = [site]

    res = wf.create_app(wf_id, app_name, app_type)
    wp_password = res['extra_info']
    print("wordpress password: %s" % wp_password)
    res = wf.create_website(wf_id, website, ip, https, subdomains, [app_name, "/"])

    try:
        site_id = res['id']
        assert(site_id)
    except:
        raise Exception("Failed to create the website :( I couldn't find an id for the website and that's all I know")

    #db_password = lib.password_creator.create(8)
    #print(wf.create_db(wf_id, app_name, "mysql", db_password))



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
    website_name = website


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
        driver.get('http://%s.sebodev.com/wp-admin/user-new.php' % website_name)

        #create the sitekeeper user
        def create_password():
            import string, random
            chars = string.ascii_letters + string.digits + string.punctuation
            passwd_size = 16
            password = ''.join((random.SystemRandom().choice(chars)) for i in range(passwd_size))
            print("the wordpress credential are now:")
            print("url: http://" + site + "/wp-admin")
            print("username: sitekeeper")
            print("password: " + password)
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
        driver.get('http://' site + "/wp-login.php?action=logout")
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
        driver.find_element_by_id("blogname").send_keys(website_name)
        driver.find_element_by_id("blogdescription").clear()
        driver.find_element_by_id("blogdescription").send_keys("")
        driver.find_element_by_id("admin_email").clear()
        driver.find_element_by_id("admin_email").send_keys("hi@sebodev.com")

        #discourage search engine crawls
        driver.get('http://' + site + "/wp-admin/options-reading.php")
        driver.find_element_by_id("blog_public").click()

        driver.find_element_by_id("submit").click()

        driver.quit()
        print('\nAll done. You know have a fancy schnazzy site to play around with.\n Just don\'t forget your username is sitekeeper and your password is %s' % password)

    except KeyboardInterrupt:
        driver.quit()
        raise
