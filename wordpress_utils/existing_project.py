'copies a theme from the webfaction server and readies the environment for dev use'


import subprocess, os, os.path
from runner import vars

#sometimes multiple themes will exist within a project. If this is the case we need to create the parent directory, otherwise the pscp command will fail.
project_parent_dir = os.path.dirname(vars.project_dir)
if not os.path.exists(project_parent_dir):
    os.makedirs(project_parent_dir)

subprocess.call(r"pscp -scp -i %UserProfile%\.ssh\sitesmash.ppk -r sebodev@webfaction:{} {}".format(vars.webfaction_theme_dir, vars.project_dir), shell=True)
print( "copied (if everything went well) {} to {}".format(vars.current_project, vars.project_dir) )
print("configuring")
from . import configure_project
