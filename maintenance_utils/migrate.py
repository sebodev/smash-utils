import lib.webfaction
from runner import vars
import subprocess
import lib.password_creator
from maintenance_utils import db_passwords

wf = wf_id = None

def main():
    migrate()

def create_db(name):
    """creates a database and database user with the name passed in.
    returns the database password"""
    user = name
    password = lib.password_creator.create(10)
    res = wf.create_db_user(wf_id, name, password, "mysql")
    print(res)
    wf.create_db(wf_id, name, "mysql", password, user)

def migrate_db(host, ssh_user, ssh_password, db, db_user, db_password, output_file):
    create_db()

    cmd = 'ssh {}@{} "mysqldump -u {} -p --database {} | gzip -c" | gzip -d > {}'.format(ssh_user, host, db_user, db, output_file)
    subprocess.run(cmd)

def migrate_files(user, host, backkup_dir, output_file):
    user = "wpwarranty"
    host = "web534.webfaction.com"
    backup_dir = "~/webapps/appName"
    output_file = tmp_dir / "backup.tar.gz"
    cmd = 'ssh {}@{} "tar -zcf – {}" > {}'.format(user, host, backup_dir, output_file)
    subprocess.run(cmd)

def migrate(server="wpwarranty"):
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
    server = input("I just need to know the name of this server. Leave empty to add a new server entry")
    if not server:
        server = lib.webfaction.interactively_add_conf_entry()


    wf, wf_id = lib.webfaction.xmlrpc_connect(server)
    migrate_db(host, ssh_user, ssh_password, db, db_user, db_password, output_file)
    migrate_files(user, host, backup_path, output_file)
