import sys

import web

from contact import contact_app

if __name__ == "__main__":
    app = contact_app()
    if "--debug" in sys.argv:
        sys.argv.remove("--debug")
        app.internalerror = web.debugerror
        app.run(web.reloader)
    else:
        app.run()
