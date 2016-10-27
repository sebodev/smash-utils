import os, os.path, sys, sqlite3
from pathlib import Path

from runner import vars
import lib.errors
from lib.errors import SmashException
from lib._passwords import _common

if os.name == 'nt':
    try:
        import win32crypt
    except:
        raise SmashException("You're going to have to install Python Extensions before you can use search through your Chrome passwords. Install the appropriate extension for your version of Python from https://sourceforge.net/projects/pywin32/files/pywin32/Build%20220/")

def find(search_term, search_term2=None):
    path = getpath()

    def query_logins_db():
        #a list of all the available fields in the db table can be found at https://cs.chromium.org/chromium/src/components/test/data/password_manager/login_db_v18.sql?sq=package:chromium
        with sqlite3.connect(path + "Login Data") as connection:
            cursor = connection.cursor()
            query_results = cursor.execute('SELECT action_url, username_value, password_value FROM logins')
            return query_results

    try:
        try:
            query_results = query_logins_db()
        except sqlite3.OperationalError:

            if vars.verbose:
                print("copying logins database to get around it being locked by a running chrome process\n")

            import shutil
            src = str(Path(path) / "Login Data")
            dest = str( vars.storage_dir / "Login Data" )
            shutil.copy(src, dest)
            if os.name == 'nt':
                path = str(vars.storage_dir) + "\\"
            else:
                path = str(vars.storage_dir) + "/"

            query_results = query_logins_db()

    except sqlite3.OperationalError as err:
        sqlErrorHandler(err)

    ret = []
    if os.name == 'nt':
        for url, user, passwd in query_results:
            if search_term in url or search_term in user:
                #unencrypts data encrypted with win32crypt.CryptProtectData. see http://docs.activestate.com/activepython/2.7/pywin32/win32crypt__CryptUnprotectData_meth.html
                password = win32crypt.CryptUnprotectData(passwd, None, None, None, 0)[1].decode()
                if search_term2:
                    if search_term2 in url or search_term2 in user:
                        ret.append(_common.credential("chrome password", url, user, password))
                else:
                    ret.append(_common.credential("chrome password", url, user, password))
    else:
        for url, user, passwd in query_results:
            if search_term2:
                if search_term2 in url or search_term2 in user:
                    ret.append(_common.credential("chrome password", url, user, password))
            else:
                ret.append(_common.credential("chrome password", url, user, password))
    if not ret:
        search_terms = search_term+" and "+search_term2 if search_term2 else search_term
        raise lib.errors.CredentialsNotFound("I've been searching long and hard, but my efforts to find a chrome password with the search term {} have failed".format(search_terms))

    return ret

def getpath():

    if os.name == "nt": #windows
        user_data_path = os.getenv('localappdata') + r'\Google\Chrome\User Data'
    elif sys.platform == "darwin": #mac
        user_data_path = os.getenv('HOME') + "/Library/Application Support/Google/Chrome"
    else: #linux
        user_data_path = os.getenv('HOME') + '/.config/google-chrome'

    #If the user has multiple Chrome profiles, we use the second one. The first one is most likely a personal profile
    #Otherwise we use the default profile
    profile_path = os.path.join(user_data_path, "Profile 1")
    if not os.path.isdir(profile_path):
        profile_path = os.path.join(user_data_path, "Default")
    if not os.path.isdir(profile_path):
        raise SmashException("Well you can't really run the chrome command if Chrome doesn't exist... Or maybe I'm just looking in the wrong spot for Chrome's user data")

    if os.name == 'nt':
        profile_path = profile_path + "\\"
    else:
        profile_path = profile_path + "/"

    return profile_path

def sqlErrorHandler(err):
    e = str(err)
    failMsg = None

    if (e == 'database is locked'):
        failMsg = "The database Chrome stores the login credentials is locked. If you're feeling persistant today, you'll have to shut down Chrome and make sure it isn't running in the background."
    elif (e == 'no such table: logins'):
        failMsg = "When we set out on a quest to find your credentials, we where unable to track down the logins database"
    elif (e == 'unable to open database file'):
        failMsg = "When we embarked on a quest to find your credentials, we discovered we where looking at the wrong file, and decided to turn around"
    else:
        failMsg = e

    raise SmashException(failMsg) from err
