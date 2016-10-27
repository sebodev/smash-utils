from lib.passwords import _common
from lib.passwords import chrome
from lib.passwords import db
from lib.passwords import filezilla
from lib.passwords import ftp
from lib.passwords import lastpass
from lib.passwords import ssh

def find(search_term, server=None):

    ret = []

    if search_term:
        try:
            ret.append(chrome.find(search_term))
        except _common.CredentialsNotFound:
            pass

        try:
            ret.append(filezilla.find(search_term))
        except _common.CredentialsNotFound:
            pass

        try:
            ret.append(lastpass.find(search_term))
        except _common.CredentialsNotFound:
            pass

    if server:
        try:
            ret.append(ftp.find(server))
        except _common.CredentialsNotFound:
            pass

        try:
            ret.append(ssh.find(server))
        except _common.CredentialsNotFound:
            pass

        try:
            ret.append(db.find(server))
        except _common.CredentialsNotFound:
            pass

    return ret
