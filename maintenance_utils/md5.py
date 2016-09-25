import os, subprocess, hashlib

def main(md5_passwd=None):
    if not md5_passwd:
        import lib.password_creator
        passwd = lib.password_creator.create(length=10)
    else:
        passwd = md5_passwd

    md5Passwd = hashlib.md5(passwd.encode('utf-8')).hexdigest()

    print(("password: " + passwd))
    print(("password hash: " + md5Passwd))
