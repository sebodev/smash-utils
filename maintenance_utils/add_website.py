import getpass, ftplib, subprocess, socket

from runner import vars
from lib import servers
from lib import webfaction
from lib import passwords
from lib import domains
import lib.errors

prompt = """
Hello {},
I'd love to keep another website on record for you.
How would you like me to look up the website?

Enter 'lastpass' to look up the website in Lastpass
Enter 'filezilla' to look up the website in Filezilla
Enter 'chrome' to look up the website in your Chrome passwords
Enter 'manual' to manually type in the website credentials
""".format(getpass.getuser())
search_for = None

def main(search_method, search_term):
    global search_for
    search_for = search_term

    if not search_method:
        search_method = input(prompt)
    search_method = search_method.lower()[0]
    credential = None

    if search_method == "l":
        wf_cred = get_credential(passwords.lastpass, "Enter a search term to find the Webfaction credential in LastPass: ")

        try:
            host = get_webserver2(wf_cred.username, wf_cred.password)
        except:
            host = input("Enter the hostname (example web353.webfaction.com): ")

        if servers.can_ftp_login(host, wf_cred.username, wf_cred.password):
            ftp_cred = wf_cred
        else:
            ftp_cred = get_credential(passwords.lastpass, "Enter a search term to find the FTP in LastPass: ")

        if servers.can_ssh_login(host, wf_cred.username, wf_cred.password):
            ssh_cred = wf_cred
        else:
            ssh_cred = get_credential(passwords.lastpass, "Enter a search term to find the SSH in LastPass: ")

    elif search_method == "f":
        ftp_cred = get_credential(passwords.filezilla)

        if servers.can_wf_login(ftp_cred.username, ftp_cred.password):
            wf_cred = ftp_cred
        else:
            wf_cred = None

        host = ftp_cred.host

        if servers.can_ssh_login(host, ftp_cred.username, ftp_cred.password):
            ssh_cred = ftp_cred
        else:
            ssh_cred = None

    elif search_method == "c":
        wf_cred = get_credential(passwords.chrome, "Enter a search term to search for the Webfaction credentials. I'll search URLs and usernames for a match: ")

        try:
            host = get_webserver2(wf_cred.username, wf_cred.password)
        except:
            host = input("Enter the hostname (example web353.webfaction.com): ")

        if servers.can_ftp_login(host, wf_cred.username, wf_cred.password):
            ftp_cred = wf_cred
        else:
            ftp_cred = None

        if servers.can_ssh_login(host, wf_cred.username, wf_cred.password):
            ssh_cred = wf_cred
        else:
            ssh_cred = None

    elif search_method == "m":
        servers.interactively_add_conf_entry()
        return

    elif search_method == "":
        raise Exception("Did not receive a response")
    else:
        raise Exception("Invalid response")

    if vars.verbose:
        print("adding", credential)

    if wf_cred:
        is_wf = servers.can_wf_login(wf_cred.username, wf_cred.password)
    else:
        is_wf = False

    if is_wf:
        name = webfaction.current_account["username"]
    else:
        name = input("What's a good name I can identify this website by. Leave blank to use {}: ".format(search_for))
        if not name:
            name = search_for

    if name in vars.servers:
        raise lib.errors.SmashException("{} already exists. Use the --edit-site command to edit it".format(name))

    servers.add_conf_entry2(
                            name,
                            ftp_cred.host,
                            ftp_cred.username,
                            ftp_cred.password,
                            ssh_cred.username,
                            ssh_cred.password,
                            wf_cred.username if wf_cred else "",
                            wf_cred.password if wf_cred else "",
                            is_webfaction=is_wf,
                            domains=[]
                            )

def get_credential(search_func, message="Enter a search term: "):
    global search_for
    credential = None
    if not search_for:
        search_for = input(message)
    assert(search_for)
    credentials = search_func(search_for)
    for i, cred in enumerate(credentials):
        print()
        print("Enter {} to use the following credential:".format(i))
        print(cred)
    res = input("\nEnter which of the above credentials you would like to use: ")
    try:
        credential = credentials[int(res)]
    except TypeError:
        raise Exception("Expected a number. Got '{}'".format(res))
    return credential
