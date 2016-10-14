'''used by new_project and existing_project to configure projects
so that the sebo --watch command will be able to keep the project
in sync with webfaction.
'''

import subprocess, os
import os.path
from runner import vars

def setup(server):
    from . import ftp_credentials
    ftp_credentials.setup_remote_sync(server)

    script = vars.script_dir / 'wordpress_utils' /'gulp_creater.py'
    subprocess.call("python %s %s %s" % (script, vars.webfaction_theme_dir, vars.project_dir / 'gulpfile.js'), shell=True)
    os.chdir(str(vars.project_dir))
    npm_packages = vars.project_dir / "packages.json"
    if npm_packages.exists():
        subprocess.call("npm start", shell=True, cwd=vars.project_dir)
    elif vars.verbose:
        print("Could not find the file %s. Skipping the npm installation. If this theme was not based off the undescores theme, this is ok." % npm_packages)
    print('-' * 80)
    print("\nCreated project %s. Happy coding.\n" % vars.current_project)
