''' runs the gulp command. If a project was specified or if we are within a project folder, we cd to that directory '''


import os.path, subprocess
from runner import smash_vars
import lib.project_info
from pathlib import Path

def main(project, theme=None):
    #raise NotImplementedError

    if not project:
        project = lib.project_info.get_project_from_dir(Path("."))

    while not project:
        print("available projects are: ")
        print(", ".join(os.listdir(str(smash_vars.projects_root_dir))))
        print()
        project = input('Enter a project to watch: ')

    while not theme:
        print("available themes are: ")
        print(", ".join(os.listdir(str(smash_vars.projects_root_dir / project))))
        print()
        theme = input('Enter a theme or plugin to watch, or leave blank to watch {}: '.format(smash_vars.projects_root_dir / project))

    project_dir = smash_vars.projects_root_dir / (project or '')
    if not project_dir.exists():
        raise Exception("couldn't run the gulp command because {} does not exist".format(project_dir))
    if not theme:
        theme = project
    if theme != project:
        project_dir = project_dir / theme
        if not project_dir.exists():
            raise Exception("couldn't run the gulp command because {} does not exist".format(project_dir))
    project_dir = str(project_dir)

    try:
        os.chdir(project_dir)
        print('watching %s' % project_dir)
        subprocess.Popen('gulp < nul', cwd=project_dir, shell=True)
    except WindowsError:
        print("Sorry, I couldn't find any gulp files at", project_dir)
