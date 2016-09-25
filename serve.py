""" starts up a server serving a web UI that exposes parts of the sebo utils tool """

import subprocess
import cherrypy
import vars
from vars import webfaction, wf_id

cherrypy.config.update({
                        'server.socket_port':   80,
                        'engine.autoreload_on': False,
                        'log.access_file':      '.\\access.log',
                        'log.error_file':       '.\\error.log',
                        'tools.staticdir.on':   False
                      })
class API(object):

    @cherrypy.expose
    def index(self):
        "returns the index page"
        return """
            <form type=get action="/createsite">
                Create a site
                <input type=text placeholder='Enter Subdomain' name=sitename /> <input type=submit> <br/>
            </form>
            """ \
            "<h4>Current Sebodev Subdomains</h4>" + \
            self.listsites() + \
            """<script> </script>""" + \
            """<style> body{font-family: sans-serif; margin-left: 15px; margin-top: 30px; line-height: 17px;} </style>"""

    @cherrypy.expose
    def createsite(self, sitename=None):
        """ creates a new wordpress site, and does some initial configuration. It takes sitename as a paramater"""
        if sitename is None:
            return "site name not provided"
        subprocess.Popen("sebo --wordpress %s" % sitename)
        return "In about 10 minutes %s.sebodev.com should be created." % sitename
        vars.change_current_project(sitename)
        import template_utils.wordpress_install

    @cherrypy.expose
    def listsites(self):
        """ lists all of the sites currently on the webfaction server """
        for site in sites:
            if site['domain'] == "sebodev.com":
                return "<br/>".join( site['subdomains'] )
        return "could not find the sebodev.com subdomains"

    @cherrypy.expose
    def api(self):
        """ displays the api docs """
        return "".join(
                        [
                         "<b> %s </b> <br/>" \
                         "&emsp; %s <br/>" % (
                                              method,
                                              getattr(API, method).__doc__ if getattr(API, method).__doc__ else "No documentation provided"
                                             )
                         for method in dir(API) if not method.startswith("__")
                        ]
                       )
sites = webfaction.list_domains(wf_id)
cherrypy.quickstart(API())
