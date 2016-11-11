''' parses the command line options, and stores the result in the args object. '''

import sys, argparse
import runner.help_formatter

usage_help_str = '''smash command [options]
Run smash --setup to install this script
'''

epilog_str = "More info can be found at http://sitesmash.com/docs/docs/maintenance/other/smash-utils/"
if len(sys.argv)>=2:
    epilog_str = None

def formatter(prog):
    return runner.help_formatter.Formatter(prog)

parser = argparse.ArgumentParser(formatter_class=formatter, epilog=epilog_str, usage=usage_help_str, add_help=False)

### nargs info ###
# nargs=? # nargs can be 0 or 1 items. It is saved as a string or None (unless a differen default has been specified)
# nargs=* # any number of items can be used. They will be saved in a list
# nargs=+ # same as nargs=* but there must be at least 1 item
# nargs=3 # nargs will only take three items and save them in a list. Any number can be used here
# if nargs is not used there must be 1 item, it's saved as a string
# add action="store_true" for 0 nargs
#see https://docs.python.org/3/library/argparse.html#nargs for more info
#
### metavar info ###
# metavar is the name to display on the help screen for the items nargs accepts. Use a tuple if there are multiple items
#

wordpress = parser.add_argument_group('Wordpress projects')
servers = parser.add_argument_group('Manage servers')
maintenance = parser.add_argument_group('Maintenance and general purpose')
passwords = parser.add_argument_group('Find a password')
other = parser.add_argument_group('Other options')

wordpress.add_argument("-_", "--_s-project", default="", help="Create a new _s project")
wordpress.add_argument("--download", "--down", nargs="*", metavar=("website", "theme-or-plugin"), default="", help="Downloads a theme. Also attempts to run npm install and to make the theme work with the atom editor's remote-sync plugin")
wordpress.add_argument("-n", "--new", help="Runs through an interactive session to help you get things setup.", action="store_true")
wordpress.add_argument("-w", "--watch", nargs="*", metavar=("project", "theme"), default="", help="runs the gulp command. If you are in any folder within a gulp it still works, and if you are not within a gulp project folder it will prompt you for one. Project will be an app name")
wordpress.add_argument("--wordpress", "--wp", nargs="*", metavar=("website", "app-type"), default="", help="sets up a new wordpress site")

servers.add_argument("--backup", nargs="+", metavar=["server-entry", "server-directory", "local_directory"], help="Performs a files and database backup. server-directory can also be a webfaction app-name.")
servers.add_argument("--db-backup", nargs="*", metavar=["server-entry", "local_directory"], help="Performs a files and database backup. server-directory can also be a webfaction app-name.")
servers.add_argument("--migrate", nargs="*", default="", metavar="", help="copies a website from one server to another. Does not work yet.")
servers.add_argument("--restore", nargs="*", default="", metavar=["server-entry", "server-directory", "sql-dump", "backup.tar.gz"], help="restores a backup. server-directory can also be a webfaction app. A website wil be created for the app if the app does not exist.")
servers.add_argument("--server", "--servers", nargs="?", default=None, metavar="domain-or-server", help="Displays info for a server entry of for the corresponding server entry for a domain or displays all server entries if nothing is passed in")

maintenance.add_argument("--dns", nargs="*", default="", const=None, metavar=("domain.com", "output.txt"), help="Does a DNS lookup and optionally saves the results to a text file")
maintenance.add_argument("--hosts", action="store_true", help="Opens the hosts file in notepad or vi")
maintenance.add_argument("--lockouts", metavar="website", help="Checks the number of ithemes security lockouts logged in a database")
maintenance.add_argument("--md5", nargs="?", default="", metavar="password", help="takes a password and outputs the md5 hash")
maintenance.add_argument("--monthly", nargs="*", default="", metavar=("website"), help="Performs part of the initial setup for a new WordPress Warranty client.")
maintenance.add_argument("--performance", nargs="+", metavar=("domain", "output file"), help="Runs a webpagetest.org performance test. Pass in a location to store the CSV results")
maintenance.add_argument("--ssh", metavar="website", help="ssh into a website or server")
maintenance.add_argument("--ssl", nargs="?", metavar="domain", help="Checks if either a domain's ssl certificate is expiring soon, or if a webfaction server entry is passed in, checks all of the domains on that server")
maintenance.add_argument("--wpw", nargs="*", default=[], metavar=("client name", "level of warranty (1, 2, or 3)"), help="Performs part of the initial setup for a new WordPress Warranty client.")

passwords.add_argument("--chrome", nargs="?", default="", metavar="search-term", help="Searches Google Chrome for passwords")
passwords.add_argument("--db", nargs="*", default="", metavar="website", help="Grabs database credentials from the site's wp-config.php file")
passwords.add_argument("--filezilla", "--fz", nargs="?", default="", metavar="entry", help="Filezilla's interface hides passwords, but if you provide the name from Filezilla's site manager, I'll tell you the password")
passwords.add_argument("--ftp", metavar="search-term", help="search the server entries, filezilla, chrome, and lastpass for matching ftp credentials")
passwords.add_argument("--lastpass", "--lp", nargs="?", default="", metavar="search-term", help="Searches Lastpass for passwords")
passwords.add_argument("--passwords", "--pass", nargs="?", default="", metavar="search-term", help="Searches Lastpass, Filezilla, and Chrome for passwords")

other.add_argument("-h", "--help", action="help", help="pass in an action to --help to get help on it")
other.add_argument("--new-credentials", help="whenever this script uses credentials, do not reuse saved credentials. You will be prompted for new credentials and the old one will be overwritten.", action="store_true")
other.add_argument("--setup", "--install", action="store_true", help="Runs through the initial setup of this script")
other.add_argument("--update", help="updates this script", action="store_true")
other.add_argument("-v", "--verbose", help="", action="store_true")

if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)

args, other_args = parser.parse_known_args()

if other_args:
    if len(sys.argv) > 2:
        raise Exception("Recieved the extra arguments %s" % " and ".join(other_args))
    else:
        raise Exception("Didn't recognize %s. Spelling mistaek?" % " and ".join(other_args))
