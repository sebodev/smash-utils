from runner import vars

def get_project_from_dir(the_dir):
    ''' returns which project a directory is inside of or None'''
    if not vars.projects_root_dir:
        return None
    try:
        return Path(the_dir).resolve().relative_to(vars.projects_root_dir).parent
    except ValueError:
        return None

def info(project, theme=None, user="sebodev"):
    '''returns a dictionary of info about a project'''

    project_dir = vars.projects_root_dir / (project or '')
    if not theme:
        theme = project
    if theme != project:
        project_dir = project_dir / theme
    webfaction_theme_dir = '/home/{}/webapps/{}/wp-content/themes/{}/'.format(user, project, theme)

    return {
            "project": project,
            "theme": theme,
            "project_dir": project_dir,
            "webfaction_theme_dir": webfaction_theme_dir
    }
