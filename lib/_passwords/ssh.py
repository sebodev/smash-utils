from lib import servers
from lib._passwords import common

def find(server_entry):
    ret = common.credential( "ssh password", servers.get(server_entry, "host"), servers.get(server_entry, "ssh-username"), servers.get(server_entry, "ssh-password") )
    if not ret:
        raise lib.errors.CredentialsNotFound("No SSH credentials for the server entry {}".format(server_entry))
    return ret
