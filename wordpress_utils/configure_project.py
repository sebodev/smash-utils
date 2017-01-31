'''used to configure projects
so that the sebo --watch command will be able to keep the project
in sync with webfaction.
'''

import subprocess, os
from pathlib import Path
import os.path
from runner import vars
from lib import project_info

def setup(server, project, theme, user):
    from . import ftp_credentials
    ftp_credentials.setup_remote_sync(server, project, theme, user)
    info = project_info.info(project, theme, user)

    script = vars.script_dir / 'wordpress_utils' /'gulp_creater.py'
    subprocess.call("python %s %s %s" % (script, info["webfaction_theme_dir"], Path(info["project_dir"]) / 'gulpfile.js'), shell=True)
    os.chdir(str(info["project_dir"]))
    npm_packages = Path(info["project_dir"]) / "packages.json"
    if npm_packages.exists():
        subprocess.call("npm start", shell=True, cwd=info["project_dir"])
    elif vars.verbose:
        print("Could not find the file %s. Skipping the npm installation. If this theme was not based off the undescores theme, this is ok." % npm_packages)
    print('-' * 80)
    print("\nCreated project for %s. Happy coding.\n" % project)
