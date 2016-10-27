from lib import lastpass
from lib._passwords import _common
from lib import errors

def find(search_term, search_term2=None, exact_match=False):
    """A generator that finds lastpass passwords by username, url, or name.
    Optionally narrow down the search by searching through the lastpass names of the results returned with search_term2
    returns the tuple (name, url, username password)"""

    ret = []
    if exact_match:
        for i in get_all_accounts():
            if str(search_term) == i.name.decode().strip():
                ret.append(_common.credential(i.name.decode('utf-8'), i.url.decode('utf-8'), i.username.decode('utf-8'), i.password.decode('utf-8')))

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
                        ret.append(_common.credential(password_obj.name.decode('utf-8'), password_obj.url.decode('utf-8'), password_obj.username.decode('utf-8'), password_obj.password.decode('utf-8')))
                        break
                else:
                    ret.append(_common.credential(password_obj.name.decode('utf-8'), password_obj.url.decode('utf-8'), password_obj.username.decode('utf-8'), password_obj.password.decode('utf-8')))
                    break

    if not ret:
        raise lib.errors.CredentialsNotFound("Couldn't find any matching lastpass credentials")

    return ret
