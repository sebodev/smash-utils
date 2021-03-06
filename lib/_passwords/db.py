import ftplib
from pathlib import Path
from runner import smash_vars
import lib.lastpass
import lib.passwords
from lib.errors import SmashException
import lib.webfaction
from lib._passwords import common
import lib.errors
from lib import servers
from lib import wp_cli
from lib import domains

def find_with_ftp_search(domain, wp_config_folder):
    #wp_config_folder = "webapps/cdcutah"
    search = server = "wpwarranty"
    search = domain
    credential = lib.passwords.get_ftp_credentials(search)
    if not credential:
        raise SmashException("Unable to login to {}'s server's because no ftp passwords where found in lastpass or filezilla for the search term '{}'".format(domain, search))
    name, host, user, password = credential
    return find2(wp_config_folder, host, user, password)

def find(server_entry, root_folder):
    """ finds the database credentials returning the tuple (name, host, user, password)
    root_folder is either the path to the wp config folder relative to the folder that opens up with a new ftp session
    or root_folder can be a Webfaction webapp instead"""
    if not root_folder:
        if root_folder is None:
            raise lib.errors.SmashException("cannot find db info becuase root_folder was equal to None")
        else:
            raise lib.errors.SmashException("cannot find db info becuase root_folder was empty")

    host = servers.get(server_entry, "host", False)
    user = servers.get(server_entry, "ftp-username", False)
    password = servers.get(server_entry, "ftp-password", False)

    try:
        return find2(root_folder, host, user, password)
    except lib.errors.CredentialsNotFound:
        name = wp_cli.run(server_entry, root_folder, "eval 'echo DB_NAME;'")
        host = wp_cli.run(server_entry, root_folder, "eval 'echo DB_HOST;'")
        user = wp_cli.run(server_entry, root_folder, "eval 'echo DB_USER;'")
        password = wp_cli.run(server_entry, root_folder, "eval 'echo DB_PASSWORD;'")
        return (name, host, user, password)
        #name, host, user, password = wp_cli.run(server_entry, root_folder, """eval 'echo DB_Name",". echo DB_HOST",". echo DB_USER",". echo DB_PASSWORD",". ;'""").split(",")

def find2(wp_config_folder, ftp_host, ftp_user, ftp_password):
    """ finds the database credentials
    wp_config_folder is relative to the directory that first opens up when you ftp into the server
    If this is a webfaction server wp_config_folder can also be a webapp
    returns the tuple (name, host, user, password)"""
    ftp_host = domains.normalize_domain(ftp_host)
    if smash_vars.verbose:
        print("retreiving db info using the ftp credentials host={} user={} password={}".format(ftp_host, ftp_user, ftp_password))

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
                try:
                    print( "Failed to cd to '{}'. Above is a list of the current directory contents \n{}".format(wp_config_folder,ftp.dir()) )
                except:
                    pass

                assert(wp_config_folder in smash_vars.servers)
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

        save_file = str(smash_vars.tmp_dir / "ftp_data")
        try:
            ftp.retrbinary("RETR " + "wp-config.php", callback)
        except ftplib.error_perm as err:
            if str(err) == "550 Failed to open file.":
                try:
                    pwd = ftp.pwd()
                except:
                    raise(err) from None
                raise SmashException("Failed to retreive the wp-config.php file from {} using FTP".format(pwd))
            else:
                raise(err) from None


        name = get_define_value(data, "DB_NAME")
        user = get_define_value(data, "DB_USER")
        password = get_define_value(data, "DB_PASSWORD")
        host = get_define_value(data, "DB_HOST")

        if not (name or user or password or host):
            raise lib.errors.CredentialsNotFound("Sorry sir, I've failed you. I couldn't find any database info in the config file.")

        return common.credential(name, host, user, password)

def find_local(wp_config_file):

    data = Path(wp_config_file).read_text()

    name = get_define_value(data, "DB_NAME")
    user = get_define_value(data, "DB_USER")
    password = get_define_value(data, "DB_PASSWORD")
    host = get_define_value(data, "DB_HOST")

    if not (name or user or password or host):
        raise lib.errors.CredentialsNotFound("Well that's not fun. I couldn't find all of the database info in the wp-config file.")

    return common.credential(name, host, user, password)

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
