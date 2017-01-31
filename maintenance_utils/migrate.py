import getpass, datetime, os, os.path, subprocess
from pathlib import Path

import lib.webfaction
from runner import vars
import lib.password_creator
from lib import servers
from lib import passwords
from lib import domains
from lib import ssh
from lib import webfaction
from lib import wp_cli
#from maintenance_utils import wordpress_install2
import lib.errors

def backup(server, server_dir, local_dir, do_db_backup=True, do_files_backup=True):

    assert do_db_backup or do_files_backup

    while not server:
        server = input('Enter the server entry we are backuping from: ')
    if server not in vars.servers:
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

    output_file = Path("{}-{}_{:%b-%d-%Y}.tar.gz".format(local_dir/server_dir.replace("\\", "-").replace("/", "-"), servers.get(server,"ftp-username"), datetime.date.today()))
    db_output_file = Path("{}_db-{}_{:%b-%d-%Y}.sql".format(local_dir/server_dir.replace("\\", "-").replace("/", "-"), servers.get(server,"ftp-username"), datetime.date.today()))

    if (output_file.is_file() and do_files_backup):
        raise lib.errors.SmashException("Whoa. That backup file already exists. You can find it at {}".format(output_file))
    if (db_output_file.is_file() and do_db_backup):
        raise lib.errors.SmashException("Whoa. That database backup already exists. You can find it at {}".format(db_output_file))

    db_name = db_host = db_user = db_password = None

    try:
        if server == "localhost":
            try:
                db_name, db_host, db_user, db_password = passwords.local_db(Path(server_dir)/"wp-config.php")
            except lib.errors.CredentialsNotFound:
                #will fail if the credentials are stored in the .env file instead of wp-config.php
                #In wich case we'll prompt the user for the necessary info for now
                pass
        else:
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
        #cmd = 'ssh {}@{} "mysqldump -u {} -p{} {} | gzip -c" | gzip -d > {}'.format(servers.get(server, "ssh-username"), servers.get(server, "host"), db_user, db_password, db_name, db_output_file)
        cmd = ssh.get_command(server, " mysqldump -u {} -p{} {} | gzip -c".format(db_user, db_password, db_name))
        cmd += ' | gzip -d > "{}"'.format(db_output_file)
        if vars.verbose:
            print("executing", cmd)
        subprocess.call(cmd, shell=True)

        if not db_output_file.is_file():
            raise lib.errors.SmashException("Failed to create the database backup. {} does not exist".format(db_output_file))
        if not db_output_file.stat().st_size > 2048:
            raise lib.errors.SmashException("Database backup file is empty")

    if do_files_backup:
        if (servers.get(server, "is-webfaction-server") and server_dir in lib.webfaction.get_webapps(server)):
            user = lib.webfaction.get_user(server)
            server_dir = "/home/{}/webapps/{}".format(user, server_dir)
            print(server_dir)

        #display the size of the backup folder
        #unless this is a locahost backup on a Windows machine. Windows takes forever to figure out the size of a folder
        if (server != "localhost" or os.name != "nt"):
            #cmd = "ssh {}@{} du -sh {}".format(servers.get(server, "ssh-username"), servers.get(server, "host"), server_dir)
            cmd = ssh.get_command(server, "du -sh {}".format(server_dir))
            if vars.verbose:
                print("executing", cmd)
            size = subprocess.check_output(cmd, shell=True).decode("utf-8")
            size_pos = size.find("G")+1
            if size_pos <= 0:
                size_pos = size.find("M")+1
            if size_pos:
                size = size[:size_pos]

            print("\n----- backing up {}B -----\n".format(size))

        flags = "zcvf" if vars.verbose else "zcf"
        #cmd = 'ssh {}@{} "tar -{} - {} -C {} . | gzip -c" > {}'.format(servers.get(server, "ssh-username"), servers.get(server, "host"), flags, server_dir, server_dir, output_file)
        #cmd = lib.ssh.get_command(server, "tar -{} - {} -C {} . | gzip -c".format(flags, server_dir, server_dir))
        cmd = lib.ssh.get_command(server, "tar -{} - {} -C {} .".format(flags, server_dir, server_dir))
        cmd += " > {}".format(output_file)
        if vars.verbose:
            print("executing", cmd)
        subprocess.run(cmd, shell=True)

        if not output_file.is_file():
            raise lib.errors.SmashException("Failed to create the backup. {} does not exist".format(db_output_file))
        if not output_file.stat().st_size > 0:
            raise lib.errors.SmashException("Backup file is empty")

    if os.name == "nt":
        subprocess.run("explorer {}".format(str(local_dir)))

    return

def restore(server, server_dir, sqlDump=None, backupFile=None):
    """backupFile and sqlDump must be .tar.gz files
    server_dir can be a webfaction app name as well, and will be created if it does not exist"""
    backupFile=False
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
        print("\nChanges will be permament\n")

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
        print("Thank you. I'll start restoring your website.")

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
            db_name, db_host, db_user, db_password = None, None, None, None
            db_name, db_host, db_user, db_password = passwords.db(server, server_dir)
            resp = input("""Would you like to use the database info:
database name: {}
database host: {}
database user: {}
database password: {}
[yes/No]: """.format(db_name, db_host, db_user, db_password))
            if not resp.lower().startswith("y"):
                prompt_for_db_info()
        except lib.errors.SmashException:
            resp = input("I couldn't detect a database on the server. Would you like me to create one [Yes/no]:")
            if not resp.startswith("n"):
                db_name, db_host, db_user, db_password = create_db(server, server_dir)
            else:
                print("Okey dokey. If I could just grab some info from you about the database, and then I'll get out of your hair.")
                prompt_for_db_info()

        print("\n---- restoring {}Kb database file ----\n".format(os.path.getsize(sqlDump) >> 10))

        #flags = "-xvf" if vars.verbose else "-xf"
        #cmd = 'ssh {}@{} "(cd {} && tar {} - | mysql -u {} -p{} {})" < {}'.format(servers.get(server, "ssh-username"), servers.get(server, "host"), server_dir, flags, db_user, db_password, db_name, sqlDump)
        cmd = 'ssh {ssh_user}@{ssh_host} "(sed s@{search}@{replace}@g | mysql -u {db_user} -p{db_password} {db_name} )" < {sqlDump}'.format(
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

    if backupFile:
        if apps and maybe_app not in apps:
            site = input("Enter the domain for the website you would like us to create, and we'll restore the backup there: ")
            wordpress_install2.create(site, server, "static_php70")

        print("---- restoring {}Mb backup ----\n".format(os.path.getsize(backupFile) >> 20))

        flags = "-zxvf" if vars.verbose else "-zxf"
        cmd = 'ssh {}@{} "(cd {} && tar {} -)" < {}'.format(servers.get(server, "ssh-username"), servers.get(server, "host"), server_dir, flags, backupFile)
        if vars.verbose:
            print("executing command " + cmd)
        subprocess.call(cmd, shell=True)

    if sqlDump:
        #create a new wp-config file with the new database credentials
        #and save a backup of the old one

        # if server == "localhost":
        #     db_name, db_host, db_user, db_pass = passwords.local_db(server_dir)
        # else:
        #     db_name, db_host, db_user, db_pass = passwords.db(server, server_dir)
        cmd = 'mv "{}/wp-config.php" "{}/wp-config.php.bckup"'.format(server_dir, server_dir)
        ssh.run2(cmd)
        wp_cli.run(server, server_dir, "core config --dbname={db_name} --dbhost={db_host} --dbuser={db_user} --dbpass={db_pass} --dbprefix=wp_")
        #wp_cli.run("core config --dbname={db_name} --dbhost={db_host} --dbuser={db_user} --dbpass={db_pass} --dbprefix=wp_ --extra-php < \"define('WP_DEBUG', true);\"")

def searchAndReplace(server, app, search=None, replace=None):
    raise NotImplemented
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

def create_db(server, name):
    """creates a database and database user with the name passed in.
    returns the database password"""
    user = name[:14]
    password = lib.password_creator.create(10)
    print("creating database with the password {}".format(password))
    wf, wf_id = webfaction.connect(server)
    res = wf.create_db_user(wf_id, user, password, "mysql")
    print(res)
    res = wf.create_db(wf_id, name[:14], "mysql", password, user)
    print(res)
    return (name, "localhost", user, password)

def migrate(from_site, to_site, migrate_db=True, migrate_files=True, use_new_db=False):

    f, f_server, f_app = domains.info(from_site)
    f_db_name, f_db_host, f_db_user, f_db_password = passwords.db(f_server, f_app)

    t, t_server, t_app = domains.info(to_site)

    if migrate_db:
        if use_new_db:
            name = input("What should I call the new db: ")
            t_db_name, t_db_host, t_db_user, t_db_password = create_db(to_site, name)
        else:
            t_db_name, t_db_host, t_db_user, t_db_password = None, None, None, None
            try:
                t_db_name, t_db_host, t_db_user, t_db_password = passwords.db(t_server, t_app)

                print()
                print("Database info for {}".format(to_site))
                print("name:", t_db_name)
                print("host:", t_db_host)
                print("user:", t_db_user)
                print("password:", t_db_password)
                print()

                resp = input("Would you like to overwrite the current database (the above database will be used) [Yes/no]: ")

                if resp.lower().startswith("n"):
                    t_db_name, t_db_host, t_db_user, t_db_password = None, None, None, None
                    raise lib.errors.SmashException("")

            except lib.errors.SmashException:
                while not t_db_name:
                    t_db_name = input("wWat's the name of the db we're migrating TO: ")
                while not t_db_host:
                    t_db_host = input("What's the db host. Leave blank for localhost: ")
                    if not t_db_host:
                        t_db_host = "localhost"
                while not t_db_user:
                    t_db_user = input("Enter the db username: ")
                while not t_db_password:
                    t_db_password = input("Enter the db password: ")

    f_user = lib.webfaction.get_user(f_server)
    f_app_dir = "/home/{}/webapps/{}".format(f_user, f_app)
    f_flags = "-zcfv" if vars.verbose else "-zcf"

    t_user = lib.webfaction.get_user(t_server)
    t_app_dir = "/home/{}/webapps/{}".format(t_user, t_app)
    t_flags = "-zxvf" if vars.verbose else "-zxf"

    search = domains.normalize_domain(from_site)
    replace = domains.normalize_domain(to_site)

    if migrate_db:
        print("migrating database")
        #cmd = 'ssh {f[ssh-username]}@{f[host]} "mysqldump -u{f_db_user} -p{f_db_password} {f_db_name}" | sed s@{search}@{replace}@g | ssh {t[ssh-username]}@{t[host]} "mysql -u{t_db_user} -p{t_db_password} {t_db_name}"'
        cmdA = "mysqldump -u{f_db_user} -p{f_db_password} {f_db_name}".format(**locals())
        cmdA = ssh.get_command(f_server, cmdA)
        cmdB = "sed s@{search}@{replace}@g".format(**locals())
        cmdC = "mysql -u{t_db_user} -p{t_db_password} {t_db_name}".format(**locals())
        cmdC = ssh.get_command(t_server, cmdC)
        cmd = "{cmdA} | {cmdB} | {cmdC}".format(**locals())

        if vars.verbose:
            print("executing command " + cmd)
        subprocess.call(cmd, shell=True)

    if migrate_files:
        cmd = "du -sh {}".format(t_app_dir)
        size = subprocess.check_output(ssh.run(t_server, cmd, dont_execute=True), shell=True).decode("utf-8")
        size_pos = size.find("G")+1
        if size_pos <= 0:
            size_pos = size.find("M")+1
        if size_pos:
            size = size[:size_pos]

        print("migrating files ({})".format(size))

        cmdA = "tar -c -C {f_app_dir} -f  - . ".format(**locals())
        cmdA = ssh.run(f_server, cmdA, dont_execute=True)
        cmdB = "tar -xf - -C {t_app_dir}".format(**locals())
        cmdB = ssh.run(t_server, cmdB, dont_execute=True)

        cmd = cmdA + " | " + cmdB

        if vars.verbose:
            print("executing command " + cmd)
        subprocess.call(cmd, shell=True)

        #remove the .user.ini file that wordfence creates. PHP will stop working if we don't do this.
        ssh.run(t_server, "rm {t_app_dir}/.user.ini".format(**locals()))

        #TODO update wp-config
        ssh.run(t_server, "mv {t_app_dir}/wp-config.php {t_app_dir}/wp-config.php.bckup".format(**locals()))
        wp_cli.run(t_server, t_app, "core config --dbname={t_db_name} --dbhost={t_db_host} --dbuser={t_db_user} --dbpass={t_db_password} --dbprefix=wp_".format(**locals()))
