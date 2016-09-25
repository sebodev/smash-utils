import lib.lastpass

def main(search_term):
    for i in lib.lastpass.find(search_term):
        print("\n%s\nusername: %s\npassword: %s\nurl: %s" % (i.name.decode('utf-8'), i.username.decode('utf-8'), i.password.decode('utf-8'), i.url.decode('utf-8')))
