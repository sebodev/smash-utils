from lib import servers
from lib._passwords import common
import lib.errors
from runner import smash_vars

def find(server_entry):
    if server_entry not in smash_vars.servers:
        raise lib.errors.CredentialsNotFound("The server entry {} doesn't exist".format(server_entry))

    ret = common.credential( "ftp password", servers.get(server_entry, "host"), servers.get(server_entry, "ftp-username"), servers.get(server_entry, "ftp-password") )
    if not ret:
        raise lib.errors.CredentialsNotFound("No FTP credentials for the server entry {}".format(server_entry))
    return ret
