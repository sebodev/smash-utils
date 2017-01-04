import subprocess
import lxml.etree
from runner import vars
from lib import passwords
from lib import servers
from lib import ssh

tmp_dir = vars.storage_dir / "tmp"

def get_lockout_data(server, db_user, db_password, database):
    """ returns the ithemes database table as xml """
    output_file = tmp_dir / (database + "_MySqlDump.xml")
    #cmd = 'ssh {}@{} "mysqldump -u {} -p{} {} wp_itsec_log --xml | gzip -c" | gzip -d > {}'.format(ssh_user, host, db_user, db_password, database, output_file)
    cmd = "mysqldump -u {} -p{} {} wp_itsec_log --xml | gzip -c".format(db_user, db_password, database)
    cmd = ssh.get_command(server, cmd)
    cmd += " | gzip -d > {}".format(output_file)
    if vars.verbose:
        print("executing", cmd)
    #cmd = 'ssh {}@{} "mysqldump -u {} -p{} {} wp_itsec_log --xml | gzip -c" | gzip -d > {}'.format(ssh_user, host, db_user, db_password, database, output_file)
    #print(cmd)
    #run the command while removing a couple of expected errors from the output
    errors = subprocess.PIPE
    out = subprocess.Popen(cmd, shell=True, stderr=errors)
    expectedError1 = "stdin: is not a tty"
    expectedError2 = "Warning: Using a password on the command line interface can be insecure."
    print(out.stderr.read().decode().replace(expectedError1, "").replace(expectedError2, "").strip())

    root = lxml.etree.parse(str(output_file))
    data = root.find(".//database/table_data")
    return data

def number_of_lockouts(server, db_user, db_password, database):
    """ returns the dictionary {lockouts:int, brute_force_attempts:int} """
    data = get_lockout_data(server, db_user, db_password, database)

    user_logging  = data.xpath("row/field[@name='log_type'][text()='user_logging']/..")
    lockouts      = data.xpath("row/field[@name='log_type'][text()='lockout']/..")
    brute_force   = data.xpath("row/field[@name='log_type'][text()='brute_force']/..")

    def get_hosts(elements):
        hosts = set()
        xpath_str = "field[@name='log_host']/text()"
        for e in elements:
            try:
                host = e.xpath(xpath_str)[0]
                hosts.add(host)
            except IndexError:
                pass
        return hosts

    return {
                # "users_logged": len(get_hosts(user_logging)),
                "lockouts": len(get_hosts(lockouts)),
                "brute_force_attempts": len(get_hosts(brute_force))
            }

def main(server, app_name):

    if not app_name:
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

    database, db_host, db_user, db_password =  passwords.db(server, app_name)
    print( number_of_lockouts(server, db_user, db_password, database) )
