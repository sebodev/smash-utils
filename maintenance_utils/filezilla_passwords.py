import os, os.path, base64
import lxml.etree
from runner import vars

def find(search_term):
    import os
    if os.name != "nt":
        raise Exception("This command doesn't work on a macs. :P") #I just need to know where the sitemanager.xml file is stored on macs/Linux

    logins_file = os.path.join(os.getenv("APPDATA"), r"FileZilla\sitemanager.xml")

    root = lxml.etree.parse(logins_file)
    matches = root.xpath(".//Server//*[contains(text(),'"+ search_term +"')]")

    found=False
    for el in matches:
        found=True
        el = el.getparent()
        host = el.find("Host").text
        user = el.find("User").text
        passwd = el.find("Pass").text
        name = el.find("Name").text
        encoding = el.find("EncodingType").text.lower()
        if encoding != "auto" and encoding != "base64":
            raise Exception("Sorry, the password was encrypted using the encryption method '%s' which I do not yet understand how to work with" % encoding)

        passwd = base64.b64decode(passwd).decode("utf-8")
        yield (name, host, user, passwd)
        
    if not found and vars.verbose:
        print("no filezilla logins found using the search term %s" % search_term)

def main(search_term):
    for name, host, user, passwd in find(search_term):
        print("\nInfo for", name)
        print("host:", host)
        print("user:", user)
        print("password:", passwd)
