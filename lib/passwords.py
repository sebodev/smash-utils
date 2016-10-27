from lib.errors import CredentialsNotFound


def all(search, server):
    from lib._passwords import all_passwords
    return all_passwords.find(search, server)

def chrome(search_term, search_term2=None):
    from lib._passwords import chrome as chrome_
    return chrome_.find(search_term, search_term2)

def db(server_entry, root_folder):
    from lib._passwords import db as db_
    return db_.find(server_entry, root_folder)

def filezilla(search_term):
    from lib._passwords import filezilla as filezilla_
    return filezilla_.find(search_term)

def ftp(server_entry):
    from lib._passwords import ftp as ftp_
    return ftp_.find(server_entry)

def lastpass(search_term, search_term2=None, exact_match=False):
    from lib._passwords import lastpass as lastpass_
    return lastpass_.find(search_term, search_term2, exact_match)

def ssh(server_entry):
    from lib._passwords import ssh as ssh_
    return ssh_.find(server_entry)




#
# The following perform a search for different types of credentials in lastpass
# I would recommend you use one of the above functions instead as searching through lastpass can easily return false positives
#

def get_ftp_credentials(search_term):
    """searches filezilla and then lastpass for ftp credentials
    and returns the first match found as a tuple in the form (name, host, user, passwd)"""
    found = list( filezilla(search_term) )
    if found:
        return found[0]

    found = list(lastpass(search_term, "ftp"))
    if found:
        p = found[0]
        return p.name.decode(), p.url.decode().lstrip("http://").lstrip("https://"), p.username.decode(), p.password.decode()
    raise CredentialsNotFound("Those FTP credentials are hidden pretty well. I cannot find them in filezilla or lastpass using the search terms '{}' and '{}'.".format(search_term, "ftp"))

def get_db_credentials(search_term, app_name):
    """uses get_ftp_credentials to find ftp credentials and then uses them to find the database credentials
    returns the first match found as a tuple in the form (name, host, user, passwd)"""
    return db(search_term, app_name)

def get_ssh_credentials(search_term):
    """searches lastpass for ssh credentials
    and returns the first match found as a tuple in the form (name, host, user, passwd)"""

    found = list(lastpass(search_term, "ssh"))
    if found:
        p = found[0]
        return p.name.decode(), p.url.decode().lstrip("http://").lstrip("https://"), p.username.decode(), p.password.decode()
    raise CredentialsNotFound("Those SSH credentials are hidden pretty well. I cannot find them in lastpass using the search terms '{}' and '{}'.".format(search_term, "ftp"))

def get_webfaction_credentials(search_term):
    """searches chrome and then lastpass for webfaction credentials
    and returns the first match found as a tuple in the form (name, host, user, passwd)"""
    found = list( filezilla(search_term, "my.webfaction.com") )
    if found:
        url, user, password = found[0]
        url = url.lstrip("http://").lstrip("https://")
        return ("ssh", url, user, password)

    found = list(lastpass(search_term, "my.webfaction.com"))
    if found:
        p = found[0]
        return p.name.decode(), p.url.decode().lstrip("http://").lstrip("https://"), p.username.decode(), p.password.decode()
    raise CredentialsNotFound("Those FTP credentials are hidden pretty well. I cannot find them in Chrome or lastpass using the search terms '{}' and '{}'.".format(search_term, "ftp"))
