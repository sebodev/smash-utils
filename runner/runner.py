''' The runner for all of the other scripts '''

import sys
from runner.get_cmd_line_options import args
from runner import smash_vars
from lib.domains import get_server_app

utils_dir = smash_vars.script_dir / "utils"
sys.path.append( str(utils_dir.resolve()) )

if "--setup" in sys.argv:
    from runner import setup
    setup.main()

elif "--temp" in sys.argv:
    #This is just a place for me to temporarily test stuff
    from general_utils import wp_users
    print(wp_users.get_password_hash(*get_server_app("staging.ujido.com"), "sitekeeper"))

elif "--change-password" in sys.argv:
    from general_utils import wp_users

    try:
        site = args.change_password[0]
    except:
        site = None

    try:
        user = args.change_password[1]
    except:
        user = None

    try:
        password = args.change_password[2]
    except:
        password = None

    while not site:
        site = input("Enter a website: ")

    while not user:
        user = input("Enter a WordPress User: ")

    if not password:
        password = input(f"What would you like {user}'s new password to be. Leave blank for a random password: ")

    if not password:
        from lib import password_creator
        password = password_creator.create(length=14)
        print(f"\nThe new password will be {password}\n")

    server, app = get_server_app(site)

    wp_users.change_password(server, app, user, password)

elif "--redirect-table" in sys.argv:
    from general_utils import redirects
    from lib.domains import normalize_domain

    try:
        old = args.redirect_table[0]
    except:
        old = None

    try:
        new = args.redirect_table[1]
    except:
        new = None

    try:
        csv = args.redirect_table[2]
    except:
        csv = None

    while not old:
        old = input("Enter the url of the old website")

    while not new:
        new = input("Enter the new site or the dev site for {}".format(old))

    csv_guess = smash_vars.storage_dir/"redirect_tables"/((normalize_domain(old).replace("/", "").replace("\\", "").replace(".", ""))+".csv")
    if not csv:
        csv = input("Enter a csv file to save the results to. Leave blank for {}".format(csv_guess))
    if not csv:
        csv = csv_guess

    redirects.main(old, new, csv)

elif "--wp-cli" in sys.argv:
    from lib import wp_cli

    try:
        site = args.wp_cli[0]
    except:
        site = None

    try:
        cmd = args.wp_cli[1]
    except:
        cmd = None

    try:
        additional_args = args.wp_cli[2:]
    except:
        additional_args = None

    if additional_args:
        cmd = cmd + " " + " ".join(additional_args)

    while not site:
        site = input("Enter a website: ")
    while not cmd:
        cmd = input("Enter a command to run: ")

    server, app = get_server_app(site)

    if not app:
        app = input("Which app is this for: ")

    print( wp_cli.run(server, app, cmd) )

elif "--updates" in sys.argv or "--update" in sys.argv:
    from maintenance_utils import updates

    try:
        site = args.update[0]
    except:
        site = None
    while not site:
        site = input("Enter a website: ")

    server, app = get_server_app(site)
    updates.main(server, app)

elif "--new" in sys.argv:
    from wordpress_utils import new
    option = new.prompt_for_task(tasks_to_run)
    sys.argv.append(option)

elif "--edit-sites" in sys.argv or "--edit-websites" in sys.argv:
    #Todo need to implement an actual way of editing website entries
    import subprocess
    subprocess.run("vi {}".format(smash_vars.servers_conf_loc), shell=True)

elif "--add" in sys.argv or "--add-site" in sys.argv or "--add-website" in sys.argv:
    from manage_smash_utils import add_website

    try:
        search_method = args.add[0]
    except:
        search_method = None

    try:
        search_term = args.add[1]
    except:
        search_term = None

    add_website.main(search_method, search_term)

elif "--site" in sys.argv or "--website" in sys.argv or "--sites" in sys.argv or "--websites" in sys.argv:
    from manage_smash_utils import server_info
    server_info.main(args.site)
    from general_utils import dns
    dns.main(args.site)

elif "--list-servers" in sys.argv:
    print( ", ".join(smash_vars.servers.keys()) )

elif "--server" in sys.argv or "--servers" in sys.argv:
    try:
        choice = args.server[0]
    except:
        choice = input("Enter an action (info, add, remove, edit, etc.): ")
    if choice == "info":
        from manage_smash_utils import server_info
        try:
            server = args.server[1]
        except IndexError:
            server = input("Enter a server: ")
        server_info.main(server)
    elif choice == "add":
        from manage_smash_utils import add_website

        try:
            search_method = args.add[0]
        except:
            search_method = None

        try:
            search_term = args.add[1]
        except:
            search_term = None

        add_website.main(search_method, search_term)
    elif choice == "remove":
        raise NotImplementedError
    elif choice == "edit":
        raise NotImplementedError

elif "--ftp" in sys.argv:
    from general_utils import ftp_info
    ftp_info.main(args.ftp)

elif "--ssh" in sys.argv:
    from general_utils import ssh_session

    try:
        site = args.ssh[0]
    except:
        site = input("Enter a website to SSH into: ")

    try:
        cmd = args.ssh[1]
    except:
        cmd = None

    if cmd:
        from lib import ssh
        server = get_server_app(site)[1]
        ssh.run(server, cmd)
    else:
        ssh_session.main(site)

elif "--scp" in sys.argv:
    from lib import scp

    try:
        server = args.scp[0]
    except:
        server = None

    try:
        remote = args.scp[1]
    except:
        remote = None

    try:
        local = args.scp[2]
    except:
        local = None

    try:
        recursive = args.scp[3]
    except:
        recursive = False

    while not server:
        server = input("Enter a server: ")

    while not remote:
        server = input("Enter a remote location to copy from: ")

    while not local:
        server = input("Enter a local location to copy to: ")

    scp.copy(server, remote, local, recursive)

elif "--hosts" in sys.argv:
    from general_utils import edit_hosts_file
    edit_hosts_file.main()

elif "--monthly" in sys.argv:
    from maintenance_utils import monthly

    try:
        domain = args.monthly[0]
    except IndexError:
        domain = None
        server = None

    if domain:
        server = get_server_app(domain)[1]

    monthly.main(domain, server)

elif "--lockouts" in sys.argv:
    from maintenance_utils import security_info

    try:
        domain = args.lockouts
    except IndexError:
        domain = None

    while not domain:
        domain = input("Enter a website: ")

    server, app_name = get_server_app(domain)

    assert server and app_name
    security_info.main(server, app_name)

elif "--backup" in sys.argv:
    from backup_restore_utils import migrate

    try:
        server = args.backup[0]
    except IndexError:
        server = None
    try:
        dir_on_server = args.backup[1]
    except IndexError:
        dir_on_server = None
    try:
        local_dir = args.backup[2]
    except IndexError:
        local_dir = None

    if server not in smash_vars.servers:
        s, a = get_server_app(server)
        if s and a:
            server = s
            if not dir_on_server:
                dir_on_server = a

    migrate.backup(server, dir_on_server, local_dir)


elif "--db-backup" in sys.argv:
    from backup_restore_utils import migrate

    try:
        server = args.db_backup[0]
    except IndexError:
        server = None

    try:
        app = args.db_backup[1]
    except IndexError:
        app = None

    try:
        local_dir = args.db_backup[2]
    except IndexError:
        local_dir = None

    migrate.backup(server, app, local_dir, do_db_backup=True, do_files_backup=False)

elif "--restore" in sys.argv:
    from backup_restore_utils import migrate

    print("Hold on buddy. We'll save you")

    try:
        server = args.restore[0]
    except IndexError:
        server = None
    try:
        server_dir = args.restore[1]
    except IndexError:
        server_dir = None
    try:
        sqlDump = args.restore[2]
    except IndexError:
        sqlDump = None
    try:
        backupFile = args.restore[3]
    except IndexError:
        backupFile = None

    migrate.restore(server, server_dir, sqlDump, backupFile)

elif "--migrate" in sys.argv:
    from backup_restore_utils import migrate

    try:
        websiteFrom = args.migrate[0]
    except IndexError:
        websiteFrom = None
    try:
        websiteTo = args.migrate[1]
    except IndexError:
        websiteTo = None

    while not websiteFrom:
        websiteFrom = input('Enter the website you are migrating from: ')
    while not websiteTo:
        websiteTo = input('Enter the website you would like to migrate to: ')

    migrate.migrate(websiteFrom, websiteTo)

elif "--db-migrate" in sys.argv:
    from backup_restore_utils import migrate

    try:
        websiteFrom = args.migrate[0]
    except IndexError:
        websiteFrom = None
    try:
        websiteTo = args.migrate[1]
    except IndexError:
        websiteTo = None

    while not websiteFrom:
        websiteFrom = input('Enter the website you are migrating from: ')
    while not websiteTo:
        websiteTo = input('Enter the website you would like to migrate to: ')

    migrate.migrate(websiteFrom, websiteTo, migrate_files=False)

elif "--staging" in sys.argv:
    from backup_restore_utils import migrate
    from maintenance_utils import wordpress_install2

    try:
        websiteFrom = args.migrate[0]
    except IndexError:
        websiteFrom = None
    try:
        websiteTo = args.migrate[1]
    except IndexError:
        websiteTo = None

    while not websiteFrom:
        websiteFrom = input('Enter the website you are migrating from: ')
    while not websiteTo:
        websiteTo = input('Enter the website you would like to migrate to: ')

    wordpress_install2.create(websiteTo, app_type="static")
    #create database
    migrate.migrate(websiteFrom, websiteTo, use_new_db=True)

elif "--performance" in sys.argv:
    from maintenance_utils import performance_test
    domain = args.performance[0]
    try:
        save_loc = args.performance[1]
    except IndexError:
        save_loc = None
    performance_test.run(domain, save_loc)

elif "--ssl" in sys.argv:
    from maintenance_utils import ssl
    ssl.main(args.ssl)

elif "--add-ssl" in sys.argv or "--add-ssl-cert" in sys.argv or "--add-ssl-certificate" in sys.argv:
    from maintenance_utils import ssl
    domain = args.add_ssl
    while not domain:
        domain = input("Enter a domain: ")
    server, app = get_server_app(domain)
    #ssl.add(server, app)

elif "--passwords" in sys.argv or "--pass" in sys.argv:
    from password_utils import all_passwords
    search_term = args.passwords
    if not search_term:
        search_term = input('Enter a search term: ')
    all_passwords.main(search_term)

elif "--filezilla" in sys.argv or "--fz" in sys.argv:
    from password_utils import filezilla_passwords
    search_term = args.filezilla
    if not search_term:
        search_term = input('Enter your Filezilla search term: ')
    filezilla_passwords.main(search_term)

elif "--lastpass" in sys.argv or "--lp" in sys.argv:
    from password_utils import lastpass_passwords

    try:
        search_term = args.lastpass[0]
    except:
        search_term = None

    try:
        search_term2 = args.lastpass[1]
    except:
        search_term2 = None

    if not search_term:
        search_term = input('Enter your Lastpass search term: ')
    lastpass_passwords.main(search_term, search_term2)

elif "--chrome" in sys.argv:
    from password_utils import chrome_passwords
    search_term = args.chrome
    if not search_term:
        search_term = input('Enter your Chrome search term: ')
    chrome_passwords.main(search_term)

elif "--db" in sys.argv:
    from password_utils import db_passwords
    try:
        site = args.db[0]
    except IndexError:
        site = input('Enter a website: ')

    server, app_name = get_server_app(site)

    db_passwords.main(server, app_name)

elif "--smash-update" in sys.argv or "--update-smash-utils" in sys.argv:
    import os, subprocess
    os.chdir(str(smash_vars.script_dir))
    subprocess.call("git pull", shell=True)

elif "--dns" in sys.argv:
    from general_utils import dns
    try:
        domain = args.dns[0]
    except IndexError:
        domain = None
    try:
        dns_output_file = args.dns[1]
    except IndexError:
        dns_output_file = None

    while not domain:
        domain = input('Enter a domain (example google.com): ')

    dns.main(domain, dns_output_file)

elif "--conf" in sys.argv:
    from maintenance_utils import confs

    try:
        site = args.confs[0]
    except IndexError:
        site = None

    confs.main(site)

elif "--wpw" in sys.argv:
    from maintenance_utils import wpw_setup
    from maintenance_utils import confs

    try:
        wpw_name = args.wpw[0]
    except IndexError:
        wpw_name = None
    try:
        wpw_level = int(args.wpw[1])
    except IndexError:
        wpw_level = None

    while not wpw_name:
        wpw_name = input('Enter a client name (example Ujido): ')
    while not wpw_level:
        wpw_level = int(input('If this is a WPW 99 client enter a 1. If this is a WPW client enter a 2. If this is a WPW and Maintenance client enter a 3: '))

    wpw_setup.main(wpw_name, wpw_level)
    confs.create_maintenance_conf(input("Enter the website domain: "), wpw_name, wpw_level)

elif ("--md5" in sys.argv or "--hash" in sys.argv):
    from general_utils import md5
    if not args.md5:
        args.md5 == input('Enter a password or leave empty for a random one: ')
    md5.main(args.md5)

elif ("--del" in sys.argv or "--delete" in sys.argv):
    from wordpress_utils import delete_site
    delete_site.main(args.delete)

elif ("--wp" in sys.argv or "--wordpress" in sys.argv):
    from wordpress_utils import wordpress_install2

    try:
        site = args.wordpress[0]
    except IndexError:
        site = None

    try:
        server = args.wordpress[1]
    except IndexError:
        server = None

    app_type = None
    try:
        app_type = args.wordpress[2]
    except IndexError:
        app_type = wordpress_install2.CURRENT_WORDPRESS_VERSION

    if server == "static":
        server = None
        app_type = "static"

    wordpress_install2.create(site, server, app_type)

    # the following is the old way of creating sites with selenium
    # from wordpress_utils import wordpress_install

elif ("--down" in sys.argv or "--download" in sys.argv):
    from wordpress_utils import download_project

    try:
        site = args.download[0]
    except IndexError:
        site = None

    try:
        theme = args.download[1]
    except IndexError:
        theme = None

    while not site:
        site = input("Enter a website: ")

    download_project.main(site, theme)

elif ("-w" in sys.argv or "--watch" in sys.argv):
    from wordpress_utils import watch

    try:
        project = args.watch[0]
    except IndexError:
        project = None

    try:
        theme_or_plugin = args.watch[1]
    except IndexError:
        theme_or_plugin = None

    watch.main(project, theme_or_plugin)
