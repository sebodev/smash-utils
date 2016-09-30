import subprocess
import lxml.etree
from runner import vars
tmp_dir = vars.storage_dir / "tmp"

def get_lockout_data(ssh_user, host, db_user, db_password, database):
    output_file = tmp_dir / (database + "_MySqlDump.xml")
    cmd = 'ssh {}@{} "mysqldump -u {} -p{} {} wp_itsec_log --xml | gzip -c" | gzip -d > {}'.format(ssh_user, host, db_user, db_password, database, output_file)

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

def main():
    ssh_user = "wpwarranty"
    host = "web534.webfaction.com"
    db_user = "cdcutah"
    db_password = "4LfOUmUN3nw3"
    database = "cdcutah"
    print( numberOfLockouts(ssh_user, host, db_user, db_password, database) )
