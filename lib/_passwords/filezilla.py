import os, os.path, base64
import lxml.etree
from runner import vars
from lib._passwords import common
import lib.errors

def find(search_term):
    import os
    if os.name != "nt":
        raise lib.errors.SmashException("This command doesn't work on a macs. :P") #I just need to know where the sitemanager.xml file is stored on macs/Linux

    logins_file = os.path.join(os.getenv("APPDATA"), r"FileZilla\sitemanager.xml")

    root = lxml.etree.parse(logins_file)
    matches = root.xpath(".//Server//*[contains(text(),'"+ search_term +"')]")
    matches = set([el.getparent() for el in matches])

    ret = []
    for el in matches:
        name = el.find("Name").text
        host = el.find("Host").text
        user = el.find("User").text
        passwd = el.find("Pass").text or ""
        encoding = el.find("EncodingType").text.lower()
        if encoding != "auto" and encoding != "base64":
            raise lib.errors.SmashException("Sorry, the password was encrypted using the encryption method '%s' which I do not yet understand how to work with" % encoding)

        passwd = base64.b64decode(passwd).decode("utf-8")

        ret.append(common.credential(name, host, user, passwd))

    if not ret:
        raise lib.errors.CredentialsNotFound("There aren't any sites saved in filezilla's site manager that includes the search term {}".format(search_term))
    return ret
