import getpass, ftplib, subprocess, socket

from runner import vars
from lib import servers
from lib import webfaction
from lib import passwords
from lib import domains

prompt = """
Hello {},
I'd love to keep another website on record for you.
How would you like me to look up the website?

Enter 'lastpass' to look up the website in Lastpass
Enter 'filezilla' to look up the website in Filezilla
Enter 'chrome' to look up the website in your Chrome passwords
Enter 'manual' to manually type in the website credentials
""".format(getpass.getuser())

def main(search):
    raise NotImplementedError() #right now the code is using the wrong value for the host. Need to login to Webfaction and grab the correct host
    res = input(prompt)
    res = res.lower()[0]
    credential = None

    if res == "l":
        wf_cred = get_credential(passwords.lastpass, "Enter a search term to find the Webfaction credential in LastPass: ")

        if can_ftp_login(wf_cred.host, wf_cred.username, wf_cred.password):
            ftp_cred = wf_cred
        else:
            ftp_cred = get_credential(passwords.lastpass, "Enter a search term to find the FTP in LastPass: ")

        if can_ssh_login(wf_cred.host, wf_cred.username, wf_cred.password):
            ssh_cred = wf_cred
        else:
            ssh_cred = get_credential(passwords.lastpass, "Enter a search term to find the SSH in LastPass: ")

    elif res == "f":
        ftp_cred = get_credential(passwords.filezilla)

        if can_wf_login(ftp_cred.username, ftp_cred.password):
            wf_cred = ftp_cred
        else:
            wf_cred = None

        if can_ssh_login(wf_cred.host, wf_cred.username, wf_cred.password):
            ssh_cred = ftp_cred
        else:
            ssh_cred = None

    elif res == "c":
        wf_cred = get_credential(passwords.chrome, "Enter a search term to search for the Webfaction credentials. I'll search URLs and usernames for a match: ")

        if can_ftp_login(wf_cred.host, wf_cred.username, wf_cred.password):
            ftp_cred = wf_cred
        else:
            ftp_cred = None

        if can_ssh_login(wf_cred.host, wf_cred.username, wf_cred.password):
            ssh_cred = wf_cred
        else:
            ssh_cred = None

    elif res == "m":
        servers.interactively_add_conf_entry()
        return
    elif res == "":
        raise Exception("Did not receive a response")
    else:
        raise Exception("Invalid response")

    if vars.verbose:
        print("adding", credential)

    is_wf = can_wf_login(wf_cred.webfaction_username, wf_cred.webfaction_password)


    servers.add_conf_entry2(
                            name,
                            wf_cred.host,
                            ftp_cred.ftp_user,
                            ftp_cred.ftp_password,
                            ssh_cred.ssh_user,
                            ssh_cred.ssh_password,
                            wf_cred.webfaction_user,
                            wf_cred.webfaction_password,
                            is_webfaction=is_wf,
                            domains=[]
                            )

def get_credential(search_func, message="Enter a search term: "):
    credential = None
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

def can_wf_login(user, password):
    try:
        webfaction.connect2(user, password)
    except lib.errors.LoginError:
        return False
    return True

def can_ftp_login(host, user, password):
    ip = socket.gethostbyname(domains.normalize_domain(host)) ############
    try:
        ftplib.FTP(ip, user, password)
    except (ftplib.error_reply, ftplib.error_temp, ftplib.error_perm):
        return False
    return True

def can_ssh_login(host, user, password):
    try:
        if os.name == "nt":
            subprocess.run("putty ssh {}@{} -pw {}".format(host, user, password))
        else:
            subprocess.run("sspass -p{} {}@{}".format(password, host, user))
    except:
        return False
    return True
