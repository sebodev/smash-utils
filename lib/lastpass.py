import os, configparser

import lib.password_creator
import lib._lastpass.vault
from runner import vars
from lib.errors import SmashException
import getpass
from lib import encoder

lastpass_username = vars.credentials_conf.get('lastpass', 'username', fallback=None)
lastpass_password = vars.credentials_conf.get('lastpass', 'password', fallback=None)
if vars.new_credentials:
    lastpass_username = lastpass_password = None

def _prompt_for_credentials():
    global lastpass_username, lastpass_password
    if not lastpass_username:
        lastpass_username = input("What's your lastpass username (your sebodev email): ")
        save_username(lastpass_username)
    elif vars.new_credentials:
        save_username(lastpass_username)

    lastpass_password = retrieve_password()
    if not lastpass_password or vars.new_credentials:
        lastpass_password = getpass.getpass("what's your lastpass password: ") #getpass behaves like input(), except the user input is not displayed on the screen
        save_password(lastpass_password)

def find_exact(name):
    """Returns the first match that where name is exactly equal to the name of a lastpass account"""
    for password_obj in get_all_accounts():
        if str(name) == password_obj.name.decode().strip():
            return password_obj

def get_all_accounts():
    global lastpass_username, lastpass_password
    if not (lastpass_username and lastpass_password):
        _prompt_for_credentials()
    else:
        lastpass_password = retrieve_password()

    try:
        vault = lib._lastpass.Vault.open_remote(lastpass_username, lastpass_password)
    except lib._lastpass.exceptions.LastPassInvalidPasswordError:
        print("Couldn't connect to LastPass. Let's give it another go.")
        lastpass_password = getpass.getpass("What's your LastPass password: ")
        vault = lib._lastpass.Vault.open_remote(lastpass_username, lastpass_password)
        save_password(lastpass_password)
    except lib._lastpass.exceptions.NetworkError:
        raise SmashException("Well shoot. Network error. LastPass must have locked us out again :( You'll have to wait a few minutes and try again.")
    return vault.accounts

def find(search_term, search_term2=None):
    """A generator that finds lastpass passwords by username, url, or name.
    Optionally narrow down the search by searching through the lastpass names of the results returned with search_term2"""
    search_term = str(search_term).lower()
    for password_obj in get_all_accounts():
        for term in search_term.split():
            if (
                    term in str(password_obj.name).lower()
                    or term in str(password_obj.url).lower()
                    or term in str(password_obj.username).lower()
                ):
                if search_term2:
                    if search_term2.lower() in str(password_obj.name).lower():
                        yield password_obj
                        break
                else:
                    yield password_obj
                    break

        #there is also password_obj.id and password_obj.group

def save_username(username):
    global lastpass_username
    lastpass_username = username
    try:
        vars.credentials_conf.set("lastpass", "username", lastpass_username)
        with vars.credentials_conf_loc.open('w') as configfile:
            vars.credentials_conf.write(configfile)
    except configparser.NoSectionError:
        vars.credentials_conf.add_section("lastpass")
        vars.credentials_conf.set("lastpass", "username", lastpass_username)
        with vars.credentials_conf_loc.open('w') as configfile:
            vars.credentials_conf.write(configfile)

def save_password(password):
    """encrypts and saves password to a config file
    only works on Windows """
    if os.name == 'nt':

        encoded2 = encoder.encrypt(password)

        vars.credentials_conf.set('lastpass', 'password', encoded2)

        with vars.credentials_conf_loc.open('w') as configfile:
            vars.credentials_conf.write(configfile)

def retrieve_password():
    """retrieves a password saved with save_password
    only works on windows"""
    if os.name == 'nt':

        password = vars.credentials_conf.get('lastpass', 'password', fallback=None)
        if not password:
            return

        return encoder.unencrypt(password)
