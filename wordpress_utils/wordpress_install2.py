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
from lib import webfaction
from lib import password_creator

def main(domain, server=None):
    if not server:
        server = "wpwarranty"

    webfaction_user = vars.webfaction[server]["ssh-username"]
    webfaction_passwd = vars.webfaction[server]["ssh-password"]
    website_name = vars.current_project.replace(' ', '')
    app_name = website_name.replace("http://", "").replace("https://", "")

    wf, wf_id = webfaction.xmlrpc_connect(server)

    print(app_name, website_name, "asdf")

    #wf.create_app(wf_id, website_name, "static_php70")
    app_name = "test"
    wf.create_website(wf_id, app_name, "75.126.24.91", False, [website_name], [app_name])
    wf.create_db(wf_id, app_name, "mysql", lib.password_creator.create(8))
