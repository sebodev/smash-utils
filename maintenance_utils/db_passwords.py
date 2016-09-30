import ftplib
from runner import vars
import lib.lastpass
import lib.passwords
from lib.errors import SmashException
import lib.webfaction

def find(domain, wp_config_folder):
    #wp_config_folder = "webapps/cdcutah"
    search = server = "wpwarranty"
    search = domain
    credential = lib.passwords.get_ftp_credentials(search)
    if not credential:
        raise SmashException("Unable to login to {}'s server's because no ftp passwords where found in lastpass or filezilla for the search term '{}'".format(domain, search))
    name, host, user, passwd = credential

    if vars.verbose:
        print("using the ftp credentials host={} user={} password={}".format(host, user, passwd))

    with ftplib.FTP(host) as ftp:
        ftp.login(user, passwd)
        #print(ftp.dir())

        try:
            ftp.cwd("webapp")
        except ftplib.error_perm as err:
            pass

        try:
            ftp.cwd(wp_config_folder)
        except ftplib.error_perm as err:
            new_err_msg = ""
            try:
                wf, wf_id = lib.webfaction.xmlrpc_connect(server)
                apps = wf.list_apps(wf_id)
                apps = [app["name"] for app in apps]
                new_err_msg = "Did not find the webfaction app {}. Possible webfaction apps are: {}".format(app_name, apps)
            except:
                raise(err)
            raise SmashException(new_err_msg)

        data = ""
        def callback(block):
            nonlocal data
            data += block.decode()

        save_file = str(vars.tmp_dir / "ftp_data")
        ftp.retrbinary("RETR " + "wp-config.php", callback)

        name = get_define_value(data, "DB_NAME")
        user = get_define_value(data, "DB_USER")
        password = get_define_value(data, "DB_PASSWORD")
        host = get_define_value(data, "DB_HOST")

        return (name, user, password, host)

def get_define_value(data, define_variable):
    ret = data[data.find(define_variable) : ]
    ret = ret[ : ret.find("\n")]

    #search for single or double quotes and trim the string to this quote until we only have the define value left

    sq = "'"
    dq = '"'

    if ret.find(sq) >= 0:
        ret = ret[ret.find(sq)+1 : ]
    else:
        ret = ret[ret.find(dq)+1 : ]

    if ret.find(sq) >= 0:
        ret = ret[ret.find(sq)+1 : ]
    else:
        ret = ret[ret.find(dq)+1 : ]

    if ret.rfind(sq) >= 0:
        ret = ret[ : ret.rfind(sq)]
    else:
        ret = ret[ : ret.rfind(dq)]
    return ret

def main(domain, app_name):
    if not app_name:
        app_name = domain.replace("http://", "").replace("https://", "").replace(".com", "").replace(".org", "")

    name, host, user, passwd = find(domain, app_name)

    print("\nDatabase name: ", name)
    print("Database host:", host)
    print("Database user:", user)
    print("Database password:", passwd)
