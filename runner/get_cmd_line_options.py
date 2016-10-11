''' parses the command line options, and stores the result in the args object.
for the wordpress commands the project name will be stored under vars.current_project '''

import sys, argparse

usage_help_str = '''smash command [options]
Run smash --setup to install this script
'''

parser = argparse.ArgumentParser(epilog="More info can be found at http://sitesmash.com/docs/docs/maintenance/other/smash-utils/", usage=usage_help_str, add_help=False)

maintenance = parser.add_argument_group('Maintenance and general purpose')
wordpress = parser.add_argument_group('Wordpress: \nA project name must be specified before using one of these options')
passwords = parser.add_argument_group('Find a password')
other = parser.add_argument_group('Other options')

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

wordpress.add_argument("-n", "--new", help="Runs through an interactive session to help you get things setup.", action="store_true")
wordpress.add_argument("-_", "--new_s-project", default="", help="Create a new _s project" )
wordpress.add_argument("--wordpress", "--wp", default="", help="sets up a new wordpress site")
wordpress.add_argument("-e", "--existing_s-project", nargs="*", metavar=("app-name", "server", "theme"), default="", help="Downloads a theme. Also attempts to run npm install and to make the theme work with the atom editor's remote-sync plugin")

maintenance.add_argument("--wpw", nargs="*", default=[], metavar=("client name", "level of warranty (1, 2, or 3)"), help="Performs part of the initial setup for a new WordPress Warranty client. Right now this just sets up a maintenance log in Google Drive.")
maintenance.add_argument("--migrate", nargs="*", help="copies a website from one server to another")
maintenance.add_argument("--dns", nargs="*", default="", const=None, metavar=("domain.com", "output.txt"), help="Does a DNS lookup and optionally saves the results to a text file")
maintenance.add_argument("--md5", nargs="?", default="", metavar="password", help="takes a password and outputs the md5 hash")
maintenance.add_argument("--ssl", nargs="?", metavar="domain", help="checks the accounts on the wpwarranty webfaction account to see if any of them are expiring soon. Optionally pass in a specific website to check")
maintenance.add_argument("--performance", nargs="+", metavar=("domain", "output file"), help="Runs a webpagetest.org performance test. Pass in a location to store the CSV results")
maintenance.add_argument("--lockouts", nargs="+", metavar=("app-name, ftp-search-term", "ssh-search-term"), help="Checks the number of ithemes security lockouts logged in a database")

passwords.add_argument("--passwords", "--pass", nargs="?", default="", metavar="search-term", help="Searches Lastpass, Filezilla, and Chrome for passwords")
passwords.add_argument("--filezilla", "--fz", nargs="?", default="", metavar="entry", help="Filezilla's interface hides passwords, but if you provide the name from Filezilla's site manager, I'll tell you the password")
passwords.add_argument("--lastpass", "--lp", nargs="?", default="", metavar="search-term", help="Searches Lastpass for passwords")
passwords.add_argument("--chrome", nargs="?", default="", metavar="search-term", help="Searches Google Chrome for passwords")
passwords.add_argument("--db", nargs="*", default="", metavar="search-term", help="Grabs database credentials from the site's wp-config.php file")

other.add_argument("--setup", "--install", action="store_true", help="Runs through the initial setup of this script")
other.add_argument("--update", help="updates this script", action="store_true")
other.add_argument("--new-credentials", help="whenever credentials are needed, prompt for them, and replace the saved credentials with the new ones", action="store_true")
other.add_argument("-v", "--verbose", help="", action="store_true")
other.add_argument("-h", "--help", action="help", help="")

if len(sys.argv) == 1:
    sys.argv.append('-h')

args, other_args = parser.parse_known_args()

# args.current_project = None

if other_args:
    if len(sys.argv) > 2:
        raise Exception("Recieved the extra arguments: %s" % " & ".join(other_args))
    else:
        raise Exception("Didn't recognize %s. Spelling mistaek?" % " and ".join(other_args))
