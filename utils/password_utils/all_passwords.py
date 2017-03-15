from runner import smash_vars
import lib.errors

import password_utils.filezilla_passwords
import password_utils.lastpass_passwords
import password_utils.chrome_passwords


def main(search_term):

    failed = []


    #filezilla
    try:
        password_utils.filezilla_passwords.main(search_term)
    except lib.errors.CredentialsNotFound:
        pass
    except Exception as err:
        failed.append("Filezilla")
        if smash_vars.verbose:
            print(err)

    #chrome
    try:
        password_utils.chrome_passwords.main(search_term)
    except lib.errors.CredentialsNotFound:
        pass
    except Exception as err:
        failed.append("Chrome")
        if smash_vars.verbose:
            print(err)

    #lastpass
    try:
        password_utils.lastpass_passwords.main(search_term)
    except lib.errors.CredentialsNotFound:
        pass
    except Exception as err:
        failed.append("Lastpass")
        if smash_vars.verbose:
            print(err)

    if failed:
        print("\n\nencountered errors while fetching passwords from " + ", ".join(failed))
        if not smash_vars.verbose:
            commands = ""
            for fail in failed:
                commands += "  smash --{} {};".format(fail, search_term)
            print("re-run the command with the -v flag to see what the errors are, \nor run the commands" + commands)
