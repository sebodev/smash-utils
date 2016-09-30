import lib.lastpass
import maintenance_utils.filezilla_passwords

def get_ftp_credentials(search_term):
    "searches filezilla and then lastpass and returns the first match found as a tuple in the form (name, host, user, passwd)"
    found = list( maintenance_utils.filezilla_passwords.find(search_term) )
    if found:
        return found[0]

    found = list(lib.lastpass.find(search_term, "ftp"))
    if found:
        p = found[0]
        return p.name.decode(), p.url.decode().lstrip("http://").lstrip("https://"), p.username.decode(), p.password.decode()
