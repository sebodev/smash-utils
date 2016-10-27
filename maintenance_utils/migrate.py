import getpass, datetime

import lib.webfaction
from runner import vars
import subprocess
import lib.password_creator
from maintenance_utils import db_passwords
from pathlib import Path
from lib import servers
from lib import errors
from lib import passwords

def backup(server, server_dir, local_dir):

    while not server:
        server = input('Enter the server entry we are backuping from: ')
    if not vars.servers.exists(server):
        print("Hello matey, we need some info about the server you're wanting to perform a backup of")
        lib.servers.interactively_add_conf_entry(server)

    while not server_dir:
        try:
            print(", ".join("\n", lib.webfaction.get_webapps(server)), "\n")
            server_dir = input("Enter which of the above webapps you would like to backup: ")
        except:
            server_dir = input('Enter the folder on the server you would like to backup: ')

    if not local_dir:
        backups_dir = vars.storage_dir / "backups"
        if not backups_dir.is_dir():
            backups_dir.mkdir()
        local_dir_default = backups_dir / servers.get(server, "ftp-username")
        local_dir = input("Enter a local folder on this computer to save the backup to. Leave blank to use {} ".format(local_dir_default))
        if not local_dir:
            local_dir = local_dir_default

    local_dir = Path(local_dir)
    if not local_dir.is_dir():
        local_dir.mkdir()

    output_file = Path("{}-{}_{:%b-%d-%Y}.tar.gz".format(local_dir/servers.get(server,"ftp-username"), server_dir.replace("\\", "-").replace("/", "-"), datetime.date.today()))
    db_output_file = Path("{}_db-{}_{:%b-%d-%Y}.sql".format(local_dir/servers.get(server,"ftp-username"), server_dir.replace("\\", "-").replace("/", "-"), datetime.date.today()))

    if (output_file.is_file() or db_output_file.is_file()):
        raise errors.SmashException("Whoa. That backup file already exists.")

    do_db_backup = True
    db_name = db_host = db_user = db_password = None

    try:
        db_name, db_host, db_user, db_password = passwords.db(server, server_dir)
    except:
        raise
        resp = input("Would you like to backup the database as well [Y/n]:")
        do_db_backup = False if resp.lower().startswith("n") else True

    if do_db_backup:
        while not db_name:
            db_name = input("what's the db name: ")
        while not db_host:
            db_host = input("what's the db host: ")
        while not db_user:
            db_user = input("what's the db username: ")
        while not db_password:
            db_password = input("what's the db password: ")

    if (server_dir in lib.webfaction.get_webapps(server)):
        user = lib.webfaction.get_user(server)
        server_dir = "/home/{}/webapps/{}".format(user, server_dir)

    cmd = 'ssh {}@{} "mysqldump -u {} -p{} {} | gzip -c" | gzip -d > {}'.format(servers.get(server, "ssh-username"), servers.get(server, "host"), db_user, db_password, db_name, db_output_file)
    subprocess.run(cmd, shell=True)

    cmd = 'ssh {}@{} "tar -zcf - {} | gzip -c" > {}'.format(servers.get(server, "ssh-username"), servers.get(server, "host"), server_dir, output_file)
    subprocess.run(cmd, shell=True)

    return

def restore(server, server_dir, sqlDump=None, backupFile=None):
    """backupFile must be a .tar.gz file
    server_dir can also be a webfaction app name"""
    if sqlDump:
        pass
    if backupFile:
        pass

def create_db(name):
    """creates a database and database user with the name passed in.
    returns the database password"""
    user = name
    password = lib.password_creator.create(10)
    res = wf.create_db_user(wf_id, name, password, "mysql")
    print(res)
    wf.create_db(wf_id, name, "mysql", password, user)

def migrate_db(from_dict, to_dict, wp_path, output_file):
    from maintenance_utils import db_passwords
    db_name, _, db_user, db_password = db_passwords.find2(wp_path, from_dict["ftp-username"], from_dict["ftp-password"])
    cmd = 'ssh {}@{} "mysqldump -u {} -p{} --database {} | gzip -c" | gzip -d > {}'.format(from_dict["ssh-username"], from_dict["host"], db_user, db_password, db_name, output_file)
    subprocess.run(cmd)

    create_db()

def migrate_files(user, host, backkup_dir, output_file):
    user = "wpwarranty"
    host = "web534.webfaction.com"
    backup_dir = "~/webapps/appName"
    output_file = tmp_dir / "backup.tar.gz"
    cmd = 'ssh {}@{} "tar -zcf – {}" > {}'.format(user, host, backup_dir, output_file)
    subprocess.run(cmd)

def migrate(serverFrom, serverTo):

    if not vars.servers.exists(serverFrom):
        print("Hello matey, we need some info from the server you are migrating FROM")
        lib.servers.interactively_add_conf_entry(serverFrom)

    if not vars.servers.exists(serverTo):
        print("Hello {}, we need some info for the server you are migrating TO".format(getpass.getuser()))
        lib.servers.interactively_add_conf_entry(serverTo)

    output_file_dir = vars.tmp_dir / "migrations"
    if not output_file_dir.is_dir():
        output_file_dir.mkdir()
    output_file = output_file_dir / vars.servers[serverFrom]["ftp-username"]+"to"+vars.servers[serverTo]["ftp-username"]

    migrate_db(vars.servers[serverFrom], vars.servers[serverTo], output_file)
    migrate_files(user, host, backup_path, output_file)

def migrateOld(serverFrom, output_file):
    """ migrate a website to a Webfaction server"""
    global wf, wf_id

    print("Hello matey, we need some info from the server you are migrating FROM")
    host = input("Enter the host you are migrating from (example web353.webfaction.com): ")
    ssh_user = input("Enter the ssh username: ")
    ssh_password = input("Enter the ssh password: ")
    backup_path = input("Enter the path to the folder you would like to backup")
    #same = input("Are the ftp credentials the same as the ssh credentials [yes/No]: "):
    if False and same.lower().startswith("n"):
        db = input("Enter the database name: ")
        db_user = input("Enter the database username: ")
        db_password = input("Enter the database password: ")
    else:
        db, db_user, db_password = db_passwords.find2(host, ssh_user, ssh_password, backup_path)

    output_file = input("Enter the location you would like to save the backup to")

    print("\n Now for the server you are copying the files to")
    serverTo = input("I just need to know the name of this server. Leave empty to add a new server entry")
    if not serverTo:
        serverTo = lib.webfaction.interactively_add_conf_entry()


    wf, wf_id = lib.webfaction.connect(server)
    migrate_db(host, ssh_user, ssh_password, db, db_user, db_password, output_file)
    migrate_files(user, host, backup_path, output_file)
