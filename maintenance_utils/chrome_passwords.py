from lib.errors import SmashException
from lib import passwords

def main(search_term):
    for credential in passwords.chrome(search_term):
        print()
        print(credential.host)
        print(credential.username)
        print(credential.password)
