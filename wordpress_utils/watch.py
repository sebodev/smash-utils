''' runs the gulp command. If a project was specified or if we are within a project folder, we cd to that directory '''


import os.path, subprocess
from runner import vars

if not vars.current_project:
    vars.change_current_project( input('Enter a project to watch: ') )
try:
    os.chdir(vars.project_dir)
    print('watching %s' % vars.project_dir)
    subprocess.Popen('gulp < nul', cwd=vars.project_dir, shell=True)
except WindowsError:
    print("Sorry, I couldn't find any gulp files at", vars.project_dir)
