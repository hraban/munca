import web

from project import *
import add
import all
import detail

urls = (
        '/robots\.txt',    'robotstxt',
        ) + add.urls + all.urls + detail.urls

class robotstxt:
    def GET(self):
        return "User-agent: *\nDisallow: /"

def contact_app():
    return web.application(urls, globals())
