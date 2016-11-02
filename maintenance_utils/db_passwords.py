import ftplib
from runner import vars
import lib.lastpass
import lib.passwords
from lib.errors import SmashException
import lib.webfaction
import lib.passwords

def find_with_ftp_search(domain, wp_config_folder):
    #wp_config_folder = "webapps/cdcutah"
    search = server = "wpwarranty"
    search = domain
    credential = lib.passwords.get_ftp_credentials(search)
    if not credential:
        raise SmashException("Unable to login to {}'s server's because no ftp passwords where found in lastpass or filezilla for the search term '{}'".format(domain, search))
    name, host, user, password = credential
    return find2(wp_config_folder, host, user, password)

def find(server_entry, wp_config_folder):
    """ finds the database credentials returning the tuple (name, host, user, password)
    wp_config_folder can be a webapp instead"""
    host = vars.servers[server_entry]["host"]
    user = vars.servers[server_entry]["ftp-username"]
    password = vars.servers[server_entry]["ftp-password"]
    return find2(wp_config_folder, host, user, password)

def find2(wp_config_folder, ftp_host, ftp_user, ftp_password):
    """ finds the database credentials
    wp_config_folder is relative to the directory that first opens up when you ftp into the server
    If this is a webfaction server wp_config_folder can also be a webapp
    returns the tuple (name, host, user, password)"""
    if vars.verbose:
        print("using the ftp credentials host={} user={} password={}".format(host, user, password))

    with ftplib.FTP(ftp_host) as ftp:
        ftp.login(ftp_user, ftp_password)
        #print(ftp.dir())
        wp_config_folder.replace("webapps/", "")
        try:
            ftp.cwd("webapps")
        except ftplib.error_perm as err:
            pass

        try:
            ftp.cwd(wp_config_folder)
        except ftplib.error_perm as err:
            new_err_msg = ""
            try:
                if vars.verbose:
                    try:
                        print( "Failed to cd to '{}'. Above is a list of the current directory contents \n{}".format(wp_config_folder,ftp.dir()) )
                    except:
                        pass
                wf, wf_id = lib.webfaction.connect(wp_config_folder) #Todo need to be able to map the host to the webfaction conf entry
                apps = wf.list_apps(wf_id)
                apps = [app["name"] for app in apps]
                new_err_msg = "Did not find the webfaction app {}. Possible webfaction apps are: {}".format(wp_config_folder, apps)
            except:
                #if we weren't able to provide a more detailed error message raise the original error message
                raise(err) from None
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

        return (name, host, user, password)

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

def main(server, app_name):
    vars.servers[server]

    if not app_name:
        app_name = server.replace("http://", "").replace("https://", "").replace(".com", "").replace(".org", "")

    name, host, user, passwd = lib.passwords.db(server, app_name)

    print("\nDatabase name: ", name)
    print("Database host:", host)
    print("Database user:", user)
    print("Database password:", passwd)
