import xmlrpc.client
from lib.errors import SmashException
from lib import lastpass
import configparser
from runner import vars
#the xmlrpc object for communicating with webfaction see https://docs.webfaction.com/xmlrpc-api/tutorial.html#getting-started and https://docs.webfaction.com/xmlrpc-api/apiref.html#method-login
#the session id will automatically be provided

def xmlrpc_connect(server):
    webfaction = xmlrpc.client.ServerProxy("https://api.webfaction.com/")
    ftp_username = vars.webfaction[server]["ftp-username"]
    ftp_password = vars.webfaction[server]["ftp-password"]
    wf_id = webfaction.login(ftp_username, ftp_password)[0]
    return webfaction, wf_id

def add_conf_entry(name, lastpass_ftp_name=None, lastpass_ssh_name=None, ssh_is_ftp=False):
    """adds a new credentials to the webfaction conf file
    name is the name by which these webfaction credentials are stored under in the conf file
    a search is also done using this name and is narrowed down by the keyword ftp or ssh
    unless lastpass_ftp_name or lastpass_ssh_name is provided in which case the lastpass
    title must exactly match lastpass_ftp_name or lastpass_ssh_name
    ssh_is_ftp can be set to True if the ftp and ssh credentials are the same"""

    if lastpass_ftp_name:
        lastpass_ftp_account = lastpass.find_exact(lastpass_ftp_name)
        if lastpass_ftp_account is None:
            raise SmashException("could not find a lastpass account with the title {}".format(lastpass_ftp_name))
    else:
        res = list(lastpass.find(name, "ftp"))
        lastpass_ftp_account = res[0]
        if (len(res) > 1):
            raise SmashException('found multiple possible entries in lastpass for "{}" with "{}" in the title. You\'ll need to Pass in the exact lastpass ftp and ssh names to this function.'.format(name, "ftp"))


    if lastpass_ssh_name:
        lastpass_ssh_account = lastpass.find_exact(lastpass_ssh_name)
        if lastpass_ssh_account is None:
            raise SmashException("could not find a lastpass account with the title {}".format(lastpass_ssh_name))
    elif ssh_is_ftp:
        lastpass_ssh_account = lastpass_ftp_account
    else:
        res = list(lastpass.find(name, "ssh"))
        lastpass_ftp_account = res[0]
        if (len(res) > 1):
            raise SmashException('found multiple possible entries in lastpass for "{}" with "{}" in the title. You\'ll need to Pass in the exact lastpass ftp and ssh names to this function.'.format(name, "ftp"))


    ftp_user = lastpass_ftp_account.username.decode()
    ftp_password = lastpass_ftp_account.password.decode()
    ssh_user = lastpass_ssh_account.username.decode()
    ssh_password = lastpass_ssh_account.password.decode()
    host = lastpass_ftp_account.url.decode().lstrip("http://")

    try:
        vars.webfaction_conf.add_section(name)
    except configparser.DuplicateSectionError:
        pass

    vars.webfaction_conf.set(name, "host", host)
    vars.webfaction_conf.set(name, "ftp-username", ftp_user)
    vars.webfaction_conf.set(name, "ftp-password", ftp_password)
    vars.webfaction_conf.set(name, "ssh-username", ssh_user)
    vars.webfaction_conf.set(name, "ssh-password", ssh_password)

    with vars.webfaction_conf_loc.open('w') as configfile:
        vars.webfaction_conf.write(configfile)

    vars.save_webfaction_conf_entries()
