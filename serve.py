import subprocess

import tornado.ioloop
import tornado.web

debug = True

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class ListServers(tornado.web.RequestHandler):
    def get(self, server=""):
        self.write( subprocess.check_output("python main.py list-servers {}".format(server)) )

class Server(tornado.web.RequestHandler):
    class Info(tornado.web.RequestHandler):
        def get(self, server=""):
            server = self.get_arguments("server")
            if not server:
                self.write("A server was not provided")
            server = server[0]
            cmd = "python main.py server info {}".format(server)
            if debug:
                print("\nExecuting", cmd, "\n")
                print(self.request.arguments)
            res = subprocess.check_output(cmd).decode("utf-8")
            res.replace("\r\n", "<br>").replace("\n", "<br>")
            res = "<html>" + res + "</html>"
            self.write( res )

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/servers/list/", ListServers),
        (r"/servers/info/", Server.Info),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.instance().stop()
