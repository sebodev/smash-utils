from lib import servers
from lib._passwords import _common
import lib.errors

def find(server_entry):
    ret = _common.credential( "ftp password", servers.get(server_entry, "host"), servers.get(server_entry, "ftp-username"), servers.get(server_entry, "ftp-password") )
    if not ret:
        raise lib.errors.CredentialsNotFound("No FTP credentials for the server entry {}".format(server_entry))
    return ret
