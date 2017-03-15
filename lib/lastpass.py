import os, configparser, getpass

import lib._lastpass.vault
from lib.errors import SmashException
from lib import encoder
from lib import passwords

#import sys
#sys.path.append(r"D:\projects\smash-utils\runner")
from runner import smash_vars

lastpass_username = smash_vars.credentials_conf.get('lastpass', 'username', fallback=None)
lastpass_password = smash_vars.credentials_conf.get('lastpass', 'password', fallback=None)
if smash_vars.new_credentials:
    lastpass_username = lastpass_password = None
accounts_cache = None

def _prompt_for_credentials():
    global lastpass_username, lastpass_password
    if not lastpass_username or smash_vars.new_credentials:
        lastpass_username = input("What's your lastpass username (your sebodev email): ")
        save_username(lastpass_username)

    try:
        lastpass_password = retrieve_password()
    except lib.errors.SmashException:
        lastpass_password = None

    if not lastpass_password or smash_vars.new_credentials:
        lastpass_password = getpass.getpass("what's your lastpass password: ") #getpass behaves like input(), except the user input is not displayed on the screen
        save_password(lastpass_password)

def find_exact(name):
    """Returns the first match that where name is exactly equal to the name of a lastpass account"""
    for password_obj in get_all_accounts():
        if str(name) == password_obj.name.decode().strip():
            return password_obj

def get_all_accounts(caching=True):
    global lastpass_username, lastpass_password, accounts_cache

    if accounts_cache and caching:
        return accounts_cache

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
        raise SmashException("Well shoot. A network error. LastPass must have locked us out again :( You'll have to wait a few minutes and try again.")

    accounts_cache = vault.accounts
    return vault.accounts

def find(search_term, search_term2=None):
    return passwords.lastpass(search_term, search_term2)

def save_username(username):
    global lastpass_username
    lastpass_username = username
    try:
        smash_vars.credentials_conf.set("lastpass", "username", lastpass_username)
        with smash_vars.credentials_conf_loc.open('w') as configfile:
            smash_vars.credentials_conf.write(configfile)
    except configparser.NoSectionError:
        smash_vars.credentials_conf.add_section("lastpass")
        smash_vars.credentials_conf.set("lastpass", "username", lastpass_username)
        with smash_vars.credentials_conf_loc.open('w') as configfile:
            smash_vars.credentials_conf.write(configfile)

def save_password(password):
    """encrypts and saves password to a config file
    only works on Windows """

    encoded2 = encoder.encrypt(password)

    smash_vars.credentials_conf.set('lastpass', 'password', encoded2)

    with smash_vars.credentials_conf_loc.open('w') as configfile:
        smash_vars.credentials_conf.write(configfile)

def retrieve_password():
    """retrieves a password saved with save_password
    may raise lib.error.SmashException
    only works on windows"""

    password = smash_vars.credentials_conf.get('lastpass', 'password', fallback=None)
    if not password:
        return

    return encoder.unencrypt(password)
