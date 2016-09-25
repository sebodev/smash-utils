'''Creates a new wordpress site on the webfaction server
'''


# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.support.ui import Select
# from selenium.common.exceptions import NoSuchElementException
# from selenium.common.exceptions import NoAlertPresentException
# from selenium.webdriver.common.action_chains import ActionChains

import os, sys, time, re
import urllib.request, urllib.parse, urllib.error, urllib.parse, unittest

from runner import vars

webfaction_user = vars.ftp_username
webfaction_passwd = vars.ftp_password
website_name = vars.current_project.replace(' ', '')
if not re.compile('^[a-zA-Z0-9\.\-]+$').search(website_name) and not website_name.startswith('-') and not website.endswith('-'):
    raise Exception('You\'re getting too fancy with your subdomain. ' \
                    'The subdomain must only contain the characters a-Z and 1-9 and dashes and periods. ' \
                    'The subdomain must also not start or end with a dash.')




try:
    # driver = webdriver.Chrome()
    # driver.implicitly_wait(30)

    if False:
        #login to webfaction
        driver.get("https://my.webfaction.com/")
        driver.find_element_by_id("id_username").clear()
        driver.find_element_by_id("id_username").send_keys(webfaction_user)
        driver.find_element_by_id("id_password").clear()
        driver.find_element_by_id("id_password").send_keys(webfaction_passwd)
        driver.find_element_by_css_selector('#loginbox button[type="submit"]').click()

        if False:
            #create the wordpress site
            driver.find_element_by_link_text("DOMAINS / WEBSITES").click()
            driver.find_element_by_link_text("Websites").click()
            driver.find_element_by_link_text("Add new website").click()
            driver.find_element_by_id("id_name").clear()
            driver.find_element_by_id("id_name").send_keys(website_name)
            driver.find_element_by_css_selector("#website_form .subdomains-tokeninput input").click()
            time.sleep(1)
            driver.find_element_by_css_selector("#website_form .subdomains-tokeninput input").clear()
            driver.find_element_by_css_selector("#website_form .subdomains-tokeninput input").send_keys(website_name + ".sebodev.com")
            time.sleep(1)
            driver.find_element_by_id('website_table').click()
            time.sleep(.5)
            driver.find_element_by_id("add-another").click()
            time.sleep(1)
            driver.find_element_by_link_text("Create a new application").click()
            time.sleep(1)

            driver.find_element_by_css_selector('#name_row > td > #id_name').clear()
            driver.find_element_by_css_selector("#name_row > td > #id_name").send_keys(website_name)
            Select(driver.find_element_by_id("id_app_category")).select_by_visible_text("WordPress")

            btn = driver.find_element_by_css_selector("div.modal-footer > div > button.submit-button")
            ActionChains(driver).move_to_element(btn).click().perform()
            print('waiting 25 seconds for the website request to submit')
            time.sleep(25)
            driver.find_element_by_css_selector("#website_form .submit-button").click()
            time.sleep(1)


        #grab the password
        driver.find_element_by_link_text("DOMAINS / WEBSITES").click() #temporary line of code
        driver.find_element_by_link_text("Applications").click()
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        driver.find_element_by_css_selector(".application .row-item[data-title~='" + website_name  + "']").click()
        wp_initial_passwd = driver.find_element_by_css_selector('#extra_info .read_only_field').text
        print('successfully created %s with the username sebodev and the temporary password %s' % (website_name+".sebodev.com", wp_initial_passwd))



    #     ###############################################
    #     ## now on to fixing up our wordpres settings ##
    #     ###############################################
    #
    #     if True:
    #         #print("There is about a 5 minute wait for your site to be created. If you notice your site is created before this time, you may push enter to continue")
    #         print('waiting 5 minutes for the site to be created...')
    #         time.sleep(300)
    #     if False:
    #         raw_input('To continue. Push enter once the site is up...')
    #
    #     driver.get('http://' + website_name + ".sebodev.com" + "/wp-admin")
    #     print('let me take a moment to make a few tweaks to your wordpress installation for you...')
    #     driver.find_element_by_id("user_login").clear()
    #     driver.find_element_by_id("user_login").send_keys("sebodev")
    #     driver.find_element_by_id("user_pass").clear()
    #     driver.find_element_by_id("user_pass").send_keys(wp_initial_passwd)
    #     driver.find_element_by_id("wp-submit").click()
    #     driver.get('http://%s.sebodev.com/wp-admin/user-new.php' % website_name)
    #
    #     #create the sitekeeper user
    #     def create_password():
    #         import string, random
    #         chars = string.letters + string.digits + string.punctuation
    #         passwd_size = 16
    #         password = ''.join((random.SystemRandom().choice(chars)) for i in range(passwd_size))
    #         print("the wordpress credential are now:")
    #         print("url: http://" + website_name + ".sebodev.com/wp-admin")
    #         print("username: sitekeeper")
    #         print("password: " + password)
    #         return password
    #     driver.find_element_by_id("user_login").clear()
    #     driver.find_element_by_id("user_login").send_keys("sitekeeper")
    #     driver.find_element_by_id("email").clear()
    #     driver.find_element_by_id("email").send_keys("hi@sebodev.com")
    #     driver.find_element_by_id("first_name").clear()
    #     driver.find_element_by_id("first_name").send_keys("Snap")
    #     driver.find_element_by_id("last_name").clear()
    #     driver.find_element_by_id("last_name").send_keys("Site")
    #     driver.find_element_by_id("url").clear()
    #     driver.find_element_by_id("url").send_keys("http://sebodev.com")
    #     driver.find_element_by_class_name('wp-generate-pw').click()
    #     password = create_password()
    #     time.sleep(.5)
    #     driver.find_element_by_id('pass1-text').click()
    #     driver.find_element_by_id('pass1-text').clear()
    #     driver.find_element_by_id('pass1-text').send_keys(password)
    #     driver.find_element_by_id("send_user_notification").click()
    #     Select(driver.find_element_by_id("role")).select_by_visible_text("Administrator")
    #     driver.find_element_by_id("createuser").click()
    #     driver.find_element_by_id("createusersub").click()
    #     driver.get('http://' + website_name + ".sebodev.com" + "/wp-login.php?action=logout")
    #     driver.find_element_by_link_text("log out").click()
    #
    #
    # #log back in and delete the sebodev user
    # #
    # driver.find_element_by_id("user_login").clear()
    # driver.find_element_by_id("user_login").send_keys("sitekeeper")
    # driver.find_element_by_id("user_pass").clear()
    # driver.find_element_by_id("user_pass").send_keys(password)
    # driver.find_element_by_id("wp-submit").click()
    #
    # if True:
    #     driver.get('http://' + website_name + ".sebodev.com" + "/wp-admin/users.php")
    #     delete = driver.find_element_by_link_text("sebodev")
    #     ActionChains(driver).move_to_element(delete).move_to_element(
    #         driver.find_element_by_class_name("submitdelete")
    #         ).click().perform()
    #
    #     driver.find_element_by_id("delete_option1").click()
    #     driver.find_element_by_id("submit").click()
    #
    # #change the permalink structure
    # driver.get('http://' + website_name + ".sebodev.com" + "/wp-admin/options-permalink.php")
    # driver.find_element_by_id("permalink_structure").clear()
    # driver.find_element_by_id("permalink_structure").send_keys("/%category%/%postname%/")
    # driver.find_element_by_id("submit").click()
    #
    # #change the blog name
    # driver.get('http://' + website_name + ".sebodev.com" + "/wp-admin/options-general.php")
    # driver.find_element_by_id("blogname").clear()
    # driver.find_element_by_id("blogname").send_keys(website_name)
    # driver.find_element_by_id("blogdescription").clear()
    # driver.find_element_by_id("blogdescription").send_keys("")
    # driver.find_element_by_id("admin_email").clear()
    # driver.find_element_by_id("admin_email").send_keys("hi@sebodev.com")
    #
    # #discourage search engine crawls
    # driver.get('http://' + website_name + ".sebodev.com" + "/wp-admin/options-reading.php")
    # driver.find_element_by_id("blog_public").click()
    #
    # driver.find_element_by_id("submit").click()

    driver.quit()
    print('\nAll done. You know have a fancy schnazzy site to play around with.\n Just don\'t forget your username is sitekeeper and your password is %s' % password)

    #TODO it would be nice to install some plugins.
    # driver.get('http://' + website_name + ".sebodev.com" + "/wp-admin/plugin-install.php")
    # driver.find_element_by_name("s").clear()
    # driver.find_element_by_name("s").send_keys("advanced custom fields")
    # driver.find_element_by_id("search-submit").click()
    #
    # driver.get('http://' + website_name + ".sebodev.com" + "/wp-admin/plugin-install.php")
    # driver.find_element_by_name("s").clear()
    # driver.find_element_by_name("s").send_keys("yoast")
    # driver.find_element_by_id("search-submit").click()
    #
    # driver.get('http://' + website_name + ".sebodev.com" + "/wp-admin/plugin-install.php")
    # driver.find_element_by_name("s").clear()
    # driver.find_element_by_name("s").send_keys("super cache")
    # driver.find_element_by_id("search-submit").click()
    #
    # driver.get('http://' + website_name + ".sebodev.com" + "/wp-admin/plugin-install.php")
    # driver.find_element_by_name("s").clear()
    # driver.find_element_by_name("s").send_keys("ewww")
    # driver.find_element_by_id("search-submit").click()
    #
    # driver.get('http://' + website_name + ".sebodev.com" + "/wp-admin/plugin-install.php")
    # driver.find_element_by_name("s").clear()
    # driver.find_element_by_name("s").send_keys("word fence")
    # driver.find_element_by_id("search-submit").click()
    # driver.find_element_by_css_selector("button.submit-button").click()

    #driver.quit()
except KeyboardInterrupt:
    driver.quit()
    raise
