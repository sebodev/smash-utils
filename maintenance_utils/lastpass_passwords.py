import lib.passwords

def main(search_term):
    for i in lib.passwords.lastpass(search_term):
        print("\n%s\nurl: %s\nusername: %s\npassword: %s" % (i.name, i.host, i.username, i.password))
