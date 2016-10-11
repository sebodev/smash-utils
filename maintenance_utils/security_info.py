import subprocess
import lxml.etree
from runner import vars
from lib import passwords

tmp_dir = vars.storage_dir / "tmp"

def get_lockout_data(ssh_user, host, db_user, db_password, database):
    output_file = tmp_dir / (database + "_MySqlDump.xml")
    cmd = 'ssh {}@{} "mysqldump -u {} -p{} {} wp_itsec_log --xml | gzip -c" | gzip -d > {}'.format(ssh_user, host, db_user, db_password, database, output_file)
    print(cmd)
    #run the command while removing a couple of expected errors from the output
    errors = subprocess.PIPE
    out = subprocess.Popen(cmd, shell=True, stderr=errors)
    expectedError1 = "stdin: is not a tty"
    expectedError2 = "Warning: Using a password on the command line interface can be insecure."
    print(out.stderr.read().decode().replace(expectedError1, "").replace(expectedError2, "").strip())

    root = lxml.etree.parse(str(output_file))
    data = root.find(".//database/table_data")
    return data

def numberOfLockouts(ssh_user, host, db_user, db_password, database):
    data = get_lockout_data(ssh_user, host, db_user, db_password, database)
    print('data', data)
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

def main(app_name, ftp_search_term, ssh_search_term=None):
    if ssh_search_term is None:
        ssh_search_term = ftp_search_term

    try:
        name, host, ssh_user, ssh_password = passwords.get_ssh_credentials(ssh_search_term)
    except passwords.CredentialsNotFound:
        if vars.verbose:
            print("could not find SSH credentials, attempting to use FTP credentials for SSH")
        try:
            name, host, ssh_user, ssh_password = passwords.get_ftp_credentials(ftp_search_term)
        except passwords.CredentialsNotFound:
            if vars.verbose:
                print("could not find FTP credentials, attempting to use webfaction credentials for SSH")
            try:
                name, host, ssh_user, ssh_password = passwords.get_ftp_credentials(ftp_search_term)
            except passwords.CredentialsNotFound:
                raise Exception("Could not find any lastpass credentials using the search term {}".format(ssh_search_term)) from None

    database, db_host, db_user, db_password =  passwords.get_db_credentials(ftp_search_term, app_name)

    # ssh_user = "wpwarranty"
    # host = "web534.webfaction.com"
    # db_user = "cdcutah"
    # db_password = "4LfOUmUN3nw3"
    # database = "cdcutah"
    print( numberOfLockouts(ssh_user, host, db_user, db_password, database) )
