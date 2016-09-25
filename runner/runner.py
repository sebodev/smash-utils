''' The runner for all of the other scripts '''

import sys
from runner.get_cmd_line_options import args
from runner import vars #oops I just overwrote a built in function. To access it use `import builtins; builtins.vars`

if "--setup" in sys.argv:
    from runner import setup
    setup.main()

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

elif "--passwords" in sys.argv:
    from maintenance_utils import passwords
    search_term = args.passwords
    if not search_term:
        search_term = input('Enter a search term: ')
    passwords.main(search_term)

elif "--filezilla" in sys.argv:
    from maintenance_utils import filezilla_passwords
    search_term - args.filezilla
    if not search_term:
        search_term = input('Enter your Filezilla search term: ')
    filezilla_passwords.main(search_term)

elif "--lastpass" in sys.argv:
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

elif "--update" in sys.argv:
    import subprocess
    subprocess.call( 'cd %s & git pull' % vars.script_dir )

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
    change_current_project(args.wordpress)
    while not vars.current_project:
        vars.change_current_project(input('Enter a project (or a subdomain): '))
    import wordpress_utils.wordpress_install

elif ("-_" in sys.argv or "--new_s-project" in sys.argv):
    change_current_project(args.new_s-project)
    while not vars.current_project:
        vars.change_current_project(input('Enter a project (or a subdomain): '))
    import wordpress_utils.new_project

elif ("-e" in sys.argv or "--existing_s-project" in sys.argv):
    change_current_project(args.existing_s-project)
    while not vars.current_project:
        vars.change_current_project(input('Enter a project (or a subdomain): '))
    import wordpress_utils.existing_project

elif ("-w" in sys.argv or "--watch" in sys.argv):
    import wordpress_utils.watch
