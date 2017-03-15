""" this module is for getting info about the projects inside of smash_vars.projects_root_dir """

from pathlib import Path
from runner import smash_vars

def get_project_from_dir(the_dir):
    ''' returns which project a directory is inside of or None'''
    if not smash_vars.projects_root_dir:
        return None
    try:
        return Path(the_dir).resolve().relative_to(smash_vars.projects_root_dir).parent
    except ValueError:
        return None

def info(project, theme=None, user=None):
    '''deprecated: returns a dictionary of info about a project'''

    project_dir = smash_vars.projects_root_dir / (project or '')
    if not theme:
        theme = project
    if theme != project:
        project_dir = project_dir / theme
    project_dir = str(project_dir)

    webfaction_theme_dir = '/home/{}/webapps/{}/wp-content/themes/{}/'.format(user, project, theme)
    webfaction_plugins_dir = '/home/{}/webapps/{}/wp-content/plugins/'.format(user, project)

    return {
            "user": user,
            "project": project,
            "theme": theme,
            "project_dir": project_dir,
            "webfaction_theme_dir": webfaction_theme_dir,
            "webfaction_plugins_dir": webfaction_plugins_dir
    }
