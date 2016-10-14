import getpass

import lib.webfaction
from runner import vars
import subprocess
import lib.password_creator
from maintenance_utils import db_passwords

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
    cmd = 'ssh {}@{} "mysqldump -u {} -p{} --database {} | gzip -c" | gzip -d > {}'.format(from_dict["ssh-username"], from_dict["host"], db_user,db_password, db_name, output_file)
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
