import lib.lastpass
from maintenance_utils import filezilla_passwords
from maintenance_utils import db_passwords
from maintenance_utils import chrome_passwords
from lib.errors import SmashException

class CredentialsNotFound(SmashException):
    """raised when searching for a password and it cannot be found"""
    pass

def get_ftp_credentials(search_term):
    """searches filezilla and then lastpass for ftp credentials
    and returns the first match found as a tuple in the form (name, host, user, passwd)"""
    found = list( filezilla_passwords.find(search_term) )
    if found:
        return found[0]

    found = list(lib.lastpass.find(search_term, "ftp"))
    if found:
        p = found[0]
        return p.name.decode(), p.url.decode().lstrip("http://").lstrip("https://"), p.username.decode(), p.password.decode()
    raise CredentialsNotFound("Those FTP credentials are hidden pretty well. I cannot find them in filezilla or lastpass using the search terms '{}' and '{}'.".format(search_term, "ftp"))

def get_db_credentials(search_term, app_name):
    """uses get_ftp_credentials to find ftp credentials and then uses them to find the database credentials
    returns the first match found as a tuple in the form (name, host, user, passwd)"""
    return db_passwords.find(search_term, app_name)

def get_ssh_credentials(search_term):
    """searches lastpass for ssh credentials
    and returns the first match found as a tuple in the form (name, host, user, passwd)"""

    found = list(lib.lastpass.find(search_term, "ssh"))
    if found:
        p = found[0]
        return p.name.decode(), p.url.decode().lstrip("http://").lstrip("https://"), p.username.decode(), p.password.decode()
    raise CredentialsNotFound("Those SSH credentials are hidden pretty well. I cannot find them in lastpass using the search terms '{}' and '{}'.".format(search_term, "ftp"))

def get_webfaction_credentials(search_term):
    """searches chrome and then lastpass for webfaction credentials
    and returns the first match found as a tuple in the form (name, host, user, passwd)"""
    found = list( filezilla_passwords.find(search_term, "my.webfaction.com") )
    if found:
        url, user, password = found[0]
        url = url.lstrip("http://").lstrip("https://")
        return ("ssh", url, user, password)

    found = list(lib.lastpass.find(search_term, "my.webfaction.com"))
    if found:
        p = found[0]
        return p.name.decode(), p.url.decode().lstrip("http://").lstrip("https://"), p.username.decode(), p.password.decode()
    raise CredentialsNotFound("Those FTP credentials are hidden pretty well. I cannot find them in Chrome or lastpass using the search terms '{}' and '{}'.".format(search_term, "ftp"))
