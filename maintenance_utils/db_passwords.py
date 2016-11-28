from runner import vars
import lib.passwords
import lib.errors

def main(server, app_name):
    try:
        name, host, user, passwd = lib.passwords.db(server, app_name)

        print("\nDatabase name: ", name)
        print("Database host:", host)
        print("Database user:", user)
        print("Database password:", passwd)
    except lib.errors.CredentialsNotFound:
        print("I couldn't find any database info for the server {} and app {}.".format(server, app_name))
