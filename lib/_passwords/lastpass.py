from lib import lastpass
from lib._passwords import common
import lib.errors

def find(search_term, search_term2=None, exact_match=False):
    """A generator that finds lastpass passwords by username, url, or name.
    Optionally narrow down the search by searching through the lastpass names of the results returned with search_term2
    returns the tuple (name, url, username password)"""

    ret = []
    if exact_match:
        for i in lastpass.get_all_accounts():
            if str(search_term) == i.name.decode().strip():
                ret.append(create_cred_obj(i))

    search_term = str(search_term).lower()
    for password_obj in lastpass.get_all_accounts():
        for term in search_term.split():
            if (
                    term in str(password_obj.name).lower()
                    or term in str(password_obj.url).lower()
                    or term in str(password_obj.username).lower()
                ):
                if search_term2:
                    if search_term2.lower() in str(password_obj.name).lower():
                        ret.append(create_cred_obj(password_obj))
                        break
                else:
                    ret.append(create_cred_obj(password_obj))
                    break

    if not ret:
        raise lib.errors.CredentialsNotFound("Couldn't find any matching lastpass credentials")

    return ret

def create_cred_obj(password_obj):
    """ changes a lastpass account object into the common.credentials object """
    po = password_obj

    name = po.name
    if name:
        name = name.decode("utf-8")

    url = po.url
    if url:
        url = url.decode("utf-8")

    username = po.username
    if username:
        username = username.decode("utf-8")

    password = po.password
    if password:
        password = password.decode("utf-8")

    return common.credential(name, url, username, password)
