import lib.errors
from lib import passwords

def main(search_term):
    try:
        for credential in passwords.chrome(search_term):
            print()
            print(credential.host)
            print(credential.username)
            print(credential.password)
    except lib.errors.CredentialsNotFound:
        print("There weren't any chrome passwords with the search term {}. Better luck next time.".format(search_term))
