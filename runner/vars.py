''' A module of useful variables consisting mainly of variables
created from command line arguments and from data in config files. '''
import configparser, sys
from pathlib import Path
from lib.errors import SmashException
from lib import project_info

def change_current_project(project, new_theme=None):
    '''deprecated. Use project_info.info() instead '''
    global current_project, project_dir, webfaction_theme_dir, theme

    info = project_info.info(project, theme=new_theme, user="sebodev")

    theme = info["theme"]
    current_project = info["project"]
    project_dir = info["project_dir"]
    webfaction_theme_dir = info["webfaction_theme_dir"]

script_dir = Path(Path(__file__).resolve().parent.parent) # just getting the parent directory of this file
storage_dir = Path.home() / '.smash-utils' #store files in here that you do not want to have committed like the user credentials config
conf_dir = storage_dir / "confs"
tmp_dir = storage_dir / "tmp"

if not storage_dir.is_dir():
    storage_dir.mkdir()

if not conf_dir.is_dir():
    conf_dir.mkdir()

if not tmp_dir.is_dir():
    tmp_dir.mkdir()

#create our config readers

credentials_conf = configparser.RawConfigParser()
credentials_conf_loc = conf_dir / "credentials.conf"
credentials_conf.read(str(credentials_conf_loc))

servers_conf = configparser.RawConfigParser()
servers_conf_loc = conf_dir / "servers.conf"
servers_conf.read(str(servers_conf_loc))

google_drive_client_secret = credentials_conf.get('google-drive', 'client-secret', fallback=None)

def save_sebo_conf_vars():
    global sebo_conf, sebo_conf_loc, projects_root_dir, storage_dir, installed
    global google_drive_smash_utils_dir, google_drive_maintenance_dir, google_drive_client_secret, google_drive_root_dir

    #read in sebo_conf
    sebo_conf = configparser.RawConfigParser()
    sebo_conf_loc = script_dir / 'sebo-utils.conf'
    sebo_conf.read(str(sebo_conf_loc))

    #save some vars from the conf file
    projects_root_dir = Path(sebo_conf.get('locations', 'project_dir', fallback=""))

    try:
        sebo_conf.add_section('setup_info')
    except configparser.DuplicateSectionError:
        pass
    installed = sebo_conf.get('setup_info', 'setup_ran', fallback="")

    #save google drive folders
    google_drive_root_dir = Path( sebo_conf.get('locations', 'google_drive', fallback="") )
    google_drive_smash_utils_dir = google_drive_root_dir / "smash-utils"
    google_drive_maintenance_dir = google_drive_root_dir / "Sebo Dev" / "WordPress Warranty & Maintanence"

    saved_storage_dir = sebo_conf.get('locations', 'stored_data', fallback=None)
    # if saved_storage_dir:
    #     storage_dir = saved_storage_dir

save_sebo_conf_vars()

#save some variables from the command line options
from runner.get_cmd_line_options import args

projects_root_dir = None
current_project = project_info.get_project_from_dir(".")
verbose = args.verbose
new_credentials = args.new_credentials

if current_project:
    change_current_project(current_project)

from lib import servers as s
#A custom dictionary class is used for the servers dictionary that will add a new entry,
#prompting the user for the necessary info,
#instead of raising a KeyError
#use the exists function to test if a key is in the dictionary
class ServersDict(dict):
    def __getitem__( self, name, prompt=True ):
        try:
            return super( ServersDict, self ).__getitem__( name )
        except KeyError as err:
            if prompt:
                if not (input("Would you like to add a new server entry for %s [Yes/no]" % name).lower().startswith("n")):
                    return s.interactively_add_conf_entry(name)
                else:
                    raise KeyError("couldn't find the server entry '{}'".format(name))

    def exists(self, server_entry):
        return bool(self.__getitem__(server_entry, False))

try:
    servers = ServersDict()
except ImportError:
    #ignore errors that happen when the smash-utils hasn't run through the setup process
    if not installed:
        pass
    else:
        raise

s.save_conf_entries()
