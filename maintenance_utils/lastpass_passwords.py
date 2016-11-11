import lib.passwords

def main(search_term):
    try:
        for i in lib.passwords.lastpass(search_term):
            print("\n%s\nurl: %s\nusername: %s\npassword: %s" % (i.name, i.host, i.username, i.password))
    except lib.errors.CredentialsNotFound:
        print("I aint got nothing. The lastpass search for {} didn't turn up any results".format(search_term))
