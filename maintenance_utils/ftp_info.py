import lib.errors
from lib import passwords
from runner import vars

def main(search):

    if vars.verbose:
        print("Searching server entries...")
    try:
        credential = passwords.ftp(search)
        if credential:
            print(credential)
    except lib.errors.CredentialsNotFound:
        pass

    if vars.verbose:
        print("Searching FileZilla...")
    try:
        for credential in passwords.filezilla(search):
            print_credential(credential)
    except lib.errors.CredentialsNotFound:
        pass

    if vars.verbose:
        print("Searching Chrome passwords...")
    try:
        for credential in passwords.chrome(search, "ftp"):
            print_credential(credential)
    except lib.errors.CredentialsNotFound:
        pass

    if vars.verbose:
        print("Searching Lastpass...")
    try:
        for credential in passwords.lastpass(search, "ftp"):
            print_credential(credential)
    except lib.errors.CredentialsNotFound:
        pass

def print_credential(cred):
    print(cred.name)
    print("host:", cred.host)
    print("username:", cred.username)
    print("password:", cred.password)
    print()
