from runner import vars
from lib.errors import SmashException

import maintenance_utils.filezilla_passwords
import maintenance_utils.lastpass_passwords
import maintenance_utils.chrome_passwords

def main(search_term):

    failed = []


    #filezilla
    try:
        maintenance_utils.filezilla_passwords.main(search_term)
    except Exception as err:
        failed.append("Filezilla")
        if vars.verbose:
            print(err)

    #chrome
    try:
        maintenance_utils.chrome_passwords.main(search_term)
    except Exception as err:
        failed.append("Chrome")
        if vars.verbose:
            print(err)

    #lastpass
    try:
        maintenance_utils.lastpass_passwords.main(search_term)
    except Exception as err:
        failed.append("Lastpass")
        if vars.verbose:
            print(err)

    if failed:
        print("\n\nencountered errors while fetching passwords from " + ", ".join(failed))
        if not vars.verbose:
            commands = ""
            for fail in failed:
                commands += "  smash --{} {};".format(fail, search_term)
            print("re-run the command with the -v flag to see what the errors are, \nor run the commands" + commands)
