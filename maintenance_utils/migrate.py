import lib.webfaction

wf, wf_id = lib.webfaction.xmlrpc_connect("webfaction")

def main():
    migrate()

def create_db():
    pass

def migrate_db():
    create_db()

def migrate_files():
    raise NotImplemented()

def migrate()
    migrate_db()
