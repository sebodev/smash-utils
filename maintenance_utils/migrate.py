import lib.webfaction
from runner import vars
import subprocess

wf, wf_id = lib.webfaction.xmlrpc_connect("wpwarranty")

def main():
    migrate()

def create_db():
    pass

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

def migrate()
    if not tmp_dir.is_dir():
        tmp_dir.mk_dir()
    migrate_db()
