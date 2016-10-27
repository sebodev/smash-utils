''' The runner for all of the other scripts '''

import sys
from runner.get_cmd_line_options import args
from runner import vars #oops I just overwrote a built in function. To access it use `import builtins; builtins.vars`

if "--setup" in sys.argv:
    from runner import setup
    setup.main()

elif "--lockouts" in sys.argv:
    from maintenance_utils import security_info

    try:
        server = args.lockouts[0]
    except IndexError:
        server = input("what server is this on (example wpwarranty): ")

    try:
        app_name = args.lockouts[1]
    except IndexError:
        from lib import webfaction
        webapps = webfaction.get_webapps(server)
        app_name = input("Enter a Webfaction app name for {}: ".format(server))
        while (app_name not in webapps):
            print()
            print("AVAILABLE APPS: ")
            print(webapps)
            print()
            print("I'd love to look that up for you, but {} isn't an app on the server {}.".format(app_name, server))
            app_name = input("I suppose I'll give you another chance. What app would you like to use: ")

    security_info.main(server, app_name)

elif "--backup" in sys.argv or "--back" in sys.argv:
    from maintenance_utils import migrate

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

    migrate.backup(server, dir_on_server, local_dir)

elif "--restore" in sys.argv:
    from maintenance_utils import migrate

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
    from maintenance_utils import migrate

    try:
        serverTo = args.migrate[0]
    except IndexError:
        serverTo = None
    try:
        serverFrom = args.migrate[1]
    except IndexError:
        serverFrom = None

    while not serverTo:
        serverTo = input('Enter the server entry you would like to migrate to: ')
    while not serverFrom:
        serverFrom = input('Enter the server entry you are migrating from: ')

    migrate.migrate(serverFrom, serverTo)

elif "--performance" in sys.argv:
    from maintenance_utils import performance_test
    domain = args.performance[0]
    try:
        save_loc = args.performance[1]
    except IndexError:
        save_loc = None
    performance_test.run(domain, save_loc)

elif "--ssl" in sys.argv:
    from maintenance_utils import ssl_check
    ssl_check.main(args.ssl)

elif "--passwords" in sys.argv or "--pass" in sys.argv:
    from maintenance_utils import all_passwords
    search_term = args.passwords
    if not search_term:
        search_term = input('Enter a search term: ')
    all_passwords.main(search_term)

elif "--filezilla" in sys.argv or "--fz" in sys.argv:
    from maintenance_utils import filezilla_passwords
    search_term = args.filezilla
    if not search_term:
        search_term = input('Enter your Filezilla search term: ')
    filezilla_passwords.main(search_term)

elif "--lastpass" in sys.argv or "--lp" in sys.argv:
    from maintenance_utils import lastpass_passwords
    search_term = args.lastpass
    if not search_term:
        search_term = input('Enter your Lastpass search term: ')
    lastpass_passwords.main(search_term)

elif "--chrome" in sys.argv:
    from maintenance_utils import chrome_passwords
    search_term = args.chrome
    if not search_term:
        search_term = input('Enter your Chrome search term: ')
    chrome_passwords.main(search_term)

elif "--db" in sys.argv:
    from maintenance_utils import db_passwords
    try:
        server = args.db[0]
    except IndexError:
        server = input('Enter a server entry: ')

    try:
        app_name = args.db[1]
    except IndexError:
        app_name = input('Enter the Webfaction App Name: ')

    db_passwords.main(server, app_name)

elif "--update" in sys.argv:
    import subprocess
    print('cd %s & git pull' % vars.script_dir)
    subprocess.call( 'cd %s && git pull' % vars.script_dir )

elif "--new" in sys.argv:
    from wordpress_utils import new
    task = new.prompt_for_task(tasks_to_run)
    while not vars.current_project:
        vars.change_current_project(input('Enter a project (or a subdomain): '))
    tasks[task]()

elif "--dns" in sys.argv:
    from maintenance_utils import dns
    try:
        domain = args.dns[0]
    except IndexError:
        domain = None
    try:
        dns_output_file = args.dns[1]
    except IndexError:
        dns_output_file = None
    while not args.dns:
        domain = args.dns = input('Enter a domain (example google.com): ')
    dns.main(domain, dns_output_file)

elif "--wpw" in sys.argv:
    from maintenance_utils import wpw_setup
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

elif ("--md5" in sys.argv or "--hash" in sys.argv):
    from maintenance_utils import md5
    if not args.md5:
        args.md5 == input('Enter a password or leave empty for a random one: ')
    md5.main(args.md5)

elif ("--wp" in sys.argv or "--wordpress" in sys.argv):

    try:
        site = args.wordpress[0]
    except IndexError:
        site = None
    while not site:
        site = input("Enter the site name (example cdc.sebodev.com)")

    try:
        server = args.wordpress[1]
    except IndexError:
        server = input('Enter a server entry. Leave blank to use the Sebodev Webfaction server: ')
        if not server:
            server = "sebodev"

    #from wordpress_utils import wordpress_install

    from wordpress_utils import wordpress_install2
    wordpress_install2.create(site, server)

elif ("-_" in sys.argv or "_s-project" in sys.argv):
    while not args._s_project:
        args._s_project = input('Enter the project name: ')
    vars.change_current_project(args._s_project)
    import wordpress_utils.new_project

elif ("--down" in sys.argv or "--download" in sys.argv):
    from wordpress_utils import existing_project
    existing_project.parse_args(args.download)

elif ("-w" in sys.argv or "--watch" in sys.argv):
    vars.change_current_project(args.watch)
    import wordpress_utils.watch
