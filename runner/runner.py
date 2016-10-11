''' The runner for all of the other scripts '''

import sys
from runner.get_cmd_line_options import args
from runner import vars #oops I just overwrote a built in function. To access it use `import builtins; builtins.vars`

if "--setup" in sys.argv:
    from runner import setup
    setup.main()

elif "--lockouts" in sys.argv:
    from maintenance_utils import security_info
    app_name = args.lockouts[0]
    try:
        ftp_search_term = args.lockouts[1]
    except:
        ftp_search_term = input("what server is this on (example wpwarranty): ")
    try:
        ssh_search_term = args.lockouts[2]
    except IndexError:
        ssh_search_term = ftp_search_term
    security_info.main(app_name, ftp_search_term, ssh_search_term)

elif "--migrate" in sys.argv:
    from maintenance_utils import migrate
    migrate.main()

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
        search_term = args.db[0]
    except IndexError:
        search_term = input('Enter a website: ')

    try:
        app_name = args.db[1]
    except IndexError:
        app_name = input('Enter the Webfaction App Name: ')

    db_passwords.main(search_term, app_name)

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
    domain = args.dns[0]
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
    while not args.wordpress:
        args.wordpress = input('Enter a project (or a subdomain): ')
    vars.change_current_project(args.wordpress)

    #from wordpress_utils import wordpress_install

    from wordpress_utils import wordpress_install2
    wordpress_install2.main(vars.current_project)

elif ("-_" in sys.argv or "--new_s-project" in sys.argv):
    while not args.new_s_project:
        args.new_s_project = input('Enter the project name: ')
    vars.change_current_project(args.new_s_project)
    import wordpress_utils.new_project

elif ("-e" in sys.argv or "--existing_s-project" in sys.argv):
    from wordpress_utils import existing_project
    try:
        app_name = args.wpw[1]
    except IndexError:
        app_name = input('Enter the Webfaction app name: ')
    try:
        server = args.wpw[1]
    except IndexError:
        server = "sebodev"
    try:
        theme = args.wpw[2]
    except IndexError:
        theme = vars.current_project


    existing_project.main(app_name, server, theme)

elif ("-w" in sys.argv or "--watch" in sys.argv):
    import wordpress_utils.watch
