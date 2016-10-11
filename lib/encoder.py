import os

import lib.drive
import lib.password_creator
from runner import vars
from lib.errors import SmashException

def encrypt(password):
    """encrypts and saves password to a config file
    only works on Windows """
    #we use a simple encryption with a password key stored by Google Drive that can only be retreieved by authenticating with Google Drive
    #and we use a built-in encryption function to windows that only can be decrypted from a program run on the computer it was encrypted from
    #I don't know if there is any such function on Macs, so we'll just revert back to the defualt behaviour of asking the for a password each time on a mac
    if os.name == 'nt':
        try:
            import win32crypt
        except:
            if vars.verbose:
                print("If you don't want to have to type in the password each time, you can install the python extension from https://sourceforge.net/projects/pywin32/files/pywin32/Build%20220/ so I can more securely save the password on the computer")
            raise SmashException("Python Extensions not installed")

        drive_dir = vars.google_drive_smash_utils_dir
        key_file = drive_dir / "lastpass-key-part1"

        if not key_file.is_file():
            if not drive_dir.is_dir():
                drive_dir.mkdir()

            key = lib.password_creator.create(20)
            key_file.write_text(key)
        else:
            key = key_file.read_text()

        encoded1 = win32crypt.CryptProtectData(password.encode()).hex()
        encoded2 = _encode(key, encoded1).hex()

        return encoded2
    else:
        raise Exception("Must be on Windows to encode passwords")

def unencrypt(password):
    """retrieves a password saved with save_password
    only works on windows"""

    if os.name != 'nt':
        raise Exception("Must be on Windows to decode passwords")

    try:
        import win32crypt
    except:
        raise SmashException("Python Extensions not installed")

    key_file = vars.google_drive_smash_utils_dir / "lastpass-key-part1"
    key = key_file.read_text()

    if not key:
        raise SmashException("Unable to retrieve decryption key from Google Drive")

    password = _decode(key, bytes.fromhex(password).decode())

    password = win32crypt.CryptUnprotectData(bytes.fromhex(password))[1]

    return password.decode()


def _encode(key, clear):
    enc = []
    for i in range(len(clear)):
        key_c = key[i % len(key)]
        enc_c = chr((ord(clear[i]) + ord(key_c)) % 256)
        enc.append(enc_c)
    return "".join(enc).encode()

def _decode(key, enc):
    dec = []
    enc = enc
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)
