import getpass, datetime, os, os.path, subprocess
from pathlib import Path

import lib.webfaction
from runner import vars
import lib.password_creator
from lib import servers
from lib import errors
from lib import passwords
#from maintenance_utils import wordpress_install2
from lib.errors import SmashException

def backup(server, server_dir, local_dir, do_db_backup=True, do_files_backup=True):

    assert(do_db_backup or do_files_backup)

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
        local_dir = input("Enter a local folder on this computer to save the backup to. Leave blank to use {}: ".format(local_dir_default))
        if not local_dir:
            local_dir = local_dir_default

    local_dir = Path(local_dir)
    if not local_dir.is_dir():
        local_dir.mkdir()

    output_file = Path("{}-{}_{:%b-%d-%Y}.tar.gz".format(local_dir/servers.get(server,"ftp-username"), server_dir.replace("\\", "-").replace("/", "-"), datetime.date.today()))
    db_output_file = Path("{}_db-{}_{:%b-%d-%Y}.sql".format(local_dir/servers.get(server,"ftp-username"), server_dir.replace("\\", "-").replace("/", "-"), datetime.date.today()))

    if (output_file.is_file() and do_files_backup):
        raise errors.SmashException("Whoa. That backup file already exists. You can find it at {}".format(output_file))
    if (db_output_file.is_file() and do_db_backup):
        raise errors.SmashException("Whoa. That database backup already exists. You can find it at {}".format(db_output_file))

    db_name = db_host = db_user = db_password = None

    try:
        db_name, db_host, db_user, db_password = passwords.db(server, server_dir)
    except:
        raise
        resp = input("Would you like to backup the database as well [Yes/no]: ")
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

    if do_db_backup:
        cmd = 'ssh {}@{} "mysqldump -u {} -p{} {} | gzip -c" | gzip -d > {}'.format(servers.get(server, "ssh-username"), servers.get(server, "host"), db_user, db_password, db_name, db_output_file)
        subprocess.call(cmd, shell=True)

        if not db_output_file.is_file():
            raise SmashException("Failed to create the database backup. {} does not exist".format(db_output_file))
        if not db_output_file.stat().st_size > 2048:
            raise SmashException("Database backup file is empty")

    if do_files_backup:
        if (server_dir in lib.webfaction.get_webapps(server)):
            user = lib.webfaction.get_user(server)
            server_dir = "/home/{}/webapps/{}".format(user, server_dir)

        cmd = "ssh {}@{} du -sh {}".format(servers.get(server, "ssh-username"), servers.get(server, "host"), server_dir)
        size = subprocess.check_output(cmd, shell=True).decode("utf-8")
        size_pos = size.find("G")+1
        if size_pos <= 0:
            size_pos = size.find("M")+1
        if size_pos:
            size = size[:size_pos]

        print("\n----- backing up {} -----\n".format(size))

        flags = "zcfv" if vars.verbose else "zcf"
        cmd = 'ssh {}@{} "tar -{} - {} -C {} . | gzip -c" > {}'.format(servers.get(server, "ssh-username"), servers.get(server, "host"), flags, server_dir, server_dir, output_file)
        subprocess.run(cmd, shell=True)

        if not output_file.is_file():
            raise SmashException("Failed to create the backup. {} does not exist".format(db_output_file))
        if not output_file.stat().st_size > 0:
            raise SmashException("Backup file is empty")

    if os.name == "nt":
        subprocess.run("explorer {}".format(str(local_dir)))

    return

def restore(server, server_dir, sqlDump=None, backupFile=None):
    """backupFile and sqlDump must be .tar.gz files
    server_dir can be a webfaction app name as well, and will be created if it does not exist"""
    while not server:
        server = input("which server will we be restoring to today: ")

    if (sqlDump and backupFile):
        if sqlDump.endswith(".tar.gz") and backupFile.endswith(".sql"):
            print("I wanted the sql file first, and then the tar.gz file, but that's fine. I'll fix it.")
            sqlDump, backupFile = backupFile, sqlDump

    apps = None
    while not server_dir:
        try:
            apps = lib.webfaction.get_webapps()
            print("The following apps are currently installed on the server:")
            print(apps)
            print()
        except:
            pass
        server_dir = input("which webfaction app or which directory will we be restoring to: ")

    maybe_app = server_dir
    if lib.webfaction.can_login(server):
        server_dir = "/home/{}/webapps/{}".format(lib.webfaction.get_user(server), server_dir)

    try:
        domains = lib.webfaction.get_domains(server, maybe_app)
        print("\n{} will be permamently changed\n".format(" and ".join(domains)))
    except:
        print("\nThe server will be permamently changed. Muahaha.\n")

    if not sqlDump:
        resp = input("would you like to restore the database [Yes/no]: ")
        if not resp.startswith("n"):
            while not sqlDump:
                sqlDump = input("where is the sql file you would like to restore: ")

    if not backupFile:
        resp = input("would you like to restore the files [Yes/no]: ")
        if not resp.startswith("n"):
            while not backupFile:
                backupFile = input("where is the .tar.gz file you would like to restore: ")

    if sqlDump:
        print("We need some info to be able to perform a search and replace on the database URLs.")
        search = input("Enter a search term: ")
        replace = input("What would you like to replace {} with: ".format(search))
        print("Thank you. I'll start backing everythin up.")

    if backupFile:
        if apps and maybe_app not in apps:
            site = input("Enter the domain for the website you would like us to create, and we'll restore the backup there: ")
            wordpress_install2.create(site, server, "static_php70")

        print("---- restoring {}Mb backup ----\n".format(os.path.getsize(backupFile) >> 20))

        flags = "-zxvf" if vars.verbose else "-zxf"
        cmd = 'ssh {}@{} "gzip -d | (cd {} && tar {} -)" < {}'.format(servers.get(server, "ssh-username"), servers.get(server, "host"), server_dir, flags, backupFile)
        if vars.verbose:
            print("executing command " + cmd)
        subprocess.call(cmd, shell=True)

    db_name, db_host, db_user, db_pass = passwords.db(server, server_dir)

    if sqlDump:

        def prompt_for_db_info():
            nonlocal db_name, db_host, db_user, db_password
            while not db_name:
                db_name = input("What's the db name: ")
            while not db_host:
                db_host = input("What's the db host: ")
            while not db_user:
                db_user = input("What's the db username: ")
            while not db_password:
                db_password = input("What's the db password: ")

        try:
            db_name, db_host, db_user, db_password = passwords.db(server, server_dir)
            resp = input("""Would you like to use the database info:
database name: {}
database host: {}
database user: {}
database password: {}
[yes/No]: """.format(db_name, db_host, db_user, db_password))
            if not resp.lower().startswith("y"):
                prompt_for_db_info()
        except errors.CredentialsNotFound:
            resp = input("I couldn't detect a database on the server. Would you like me to create one [Yes/no]:")
            if not resp.startswith("n"):
                db_name, db_host, db_user, db_password = create_db(app)
            else:
                print("Okey dokey. If I could just grab some info from you about the database, and then I'll get out of your hair.")
                prompt_for_db_info()

        print("\n---- restoring {}Mb database file ----\n".format(os.path.getsize(sqlDump) >> 20))

        #flags = "-xvf" if vars.verbose else "-xf"
        #cmd = 'ssh {}@{} "(cd {} && tar {} - | mysql -u {} -p{} {})" < {}'.format(servers.get(server, "ssh-username"), servers.get(server, "host"), server_dir, flags, db_user, db_password, db_name, sqlDump)
        cmd = 'ssh {ssh_user}@{ssh_host} "(mysql -u {db_user} -p{db_password} {db_name} | sed `{search}`{replace}` )" < {sqlDump}'.format(
                                                                    ssh_user=servers.get(server, "ssh-username"),
                                                                    ssh_host=servers.get(server, "host"),
                                                                    db_user=db_user,
                                                                    db_password=db_password,
                                                                    db_name=db_name,
                                                                    search=search,
                                                                    replace=replace,
                                                                    sqlDump=sqlDump
                                                                )
        if vars.verbose:
            print("executing command " + cmd)
        subprocess.run(cmd, shell=True)

        #searchAndReplace2(db_name, db_host, db_user, db_password, search=None, replace=None)

def searchAndReplace(server, app, search=None, replace=None):
    db_name, db_host, db_user, db_password = passwords.db(server, server_dir)
    return searchAndReplace2(server, db_name, db_host, db_user, db_password, search, replace)

def searchAndReplace2(server, db_name, db_host, db_user, db_password, search=None, replace=None):
    raise NotImplemented
    if not search:
        search = input("Enter a database search term: ")
    if not replace:
        replace = input("Enter what you would like to replace {} with: ".format(search))

    cmd = "ssh {}@{} wp search-replace {} {} --skip-columns=guid".format(servers.get(server, "ssh-username"), servers.get(server, "ssh-password"), search, replace) #changing the guids will cause feed readers to see all of the blog posts as new unread articles
    subprocess.run(cmd)

def create_db(name):
    raise NotImplemented
    """creates a database and database user with the name passed in.
    returns the database password"""
    user = name
    password = lib.password_creator.create(10)
    res = wf.create_db_user(wf_id, name, password, "mysql")
    print(res)
    res = wf.create_db(wf_id, name, "mysql", password, user)
    print(res)
    return (name, "localhost", user, password)

def migrate_db(from_dict, to_dict, wp_path, output_file):
    raise NotImplementedError()
    db_name, _, db_user, db_password = db_passwords.find2(wp_path, from_dict["ftp-username"], from_dict["ftp-password"])
    cmd = 'ssh {}@{} "mysqldump -u {} -p{} --database {} | gzip -c" | gzip -d > {}'.format(from_dict["ssh-username"], from_dict["host"], db_user, db_password, db_name, output_file)
    subprocess.run(cmd)

    create_db()

def migrate_files(user, host, backkup_dir, output_file):
    raise NotImplementedError()
    user = "wpwarranty"
    host = "web534.webfaction.com"
    backup_dir = "~/webapps/appName"
    output_file = tmp_dir / "backup.tar.gz"
    cmd = 'ssh {}@{} "tar -zcf – {}" > {}'.format(user, host, backup_dir, output_file)
    subprocess.run(cmd)

def migrate(serverFrom, serverTo):
    raise NotImplementedError()

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
    raise NotImplementedError()
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
        serverTo = lib.servers.interactively_add_conf_entry()


    wf, wf_id = lib.webfaction.connect(server)
    migrate_db(host, ssh_user, ssh_password, db, db_user, db_password, output_file)
    migrate_files(user, host, backup_path, output_file)
