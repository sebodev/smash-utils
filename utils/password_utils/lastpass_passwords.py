import lib.passwords

def main(search_term, search_term2=None):
    try:
        for i in lib.passwords.lastpass(search_term, search_term2):
            print("\n%s\nurl: %s\nusername: %s\npassword: %s" % (i.name, i.host, i.username, i.password))
    except lib.errors.CredentialsNotFound:
        search_terms = search_term+" and "+search_term2 if search_term2 else search_term
        print('I aint got nothing. Searching lastpass for "{}" didn\'t turn up any results'.format(search_terms))
