import lib.passwords

def main(search_term):
    try:
        for name, host, user, passwd in lib.passwords.filezilla(search_term):
            print("\nInfo for", name)
            print("host:", host)
            print("user:", user)
            print("password:", passwd)
    except lib.errors.CredentialsNotFound:
        print("Well shoot. There's nothing in FileZilla's site manager that contains the word(s) {}.".format(search_term))
