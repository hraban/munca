"""This file declares and globals needed everywhere in the project.

Every module in the project can do `from project import *` to have all
necessary elements imported.

"""
import string
import time

import web

# Year of the upcoming conference. Should perhaps be a cookie or something.
g_year = 2009

render = web.template.render("templates/", cache=False)

db = web.database(
        dbn="postgres",
        user="user",
        pw="seekrit",
        db="unisca_contact",
    )

_alphanum = set(string.ascii_letters + string.digits + "_")
def check_table_sort(i):
    """Check if values in given web.input are suitable for ordering tables."""
    if (set(i.sort) - _alphanum) or i.order not in ("asc", "desc"):
        raise ValueError, "Can not sort table with given parameters."

def del_contact(id):
    db.delete("contact_base", where="contact_id = $id", vars=locals())
    return "Contact #%s succesfully deleted." % id

def p_name(p):
    """Return given person's full name as a string."""
    return " ".join((n for n in (p.person_firstname, p.person_surnameprefix,
            p.person_lastname) if n))

def nl2br(txt):
    return web.htmlquote(txt).replace("\r\n", "<br>").replace("\n", "<br>")

# Template globals (sorry ^^)
web.template.Template.globals['nl2br'] = nl2br
web.template.Template.globals['p_name'] = p_name
web.template.Template.globals['py'] = web.storify(__builtins__)
web.template.Template.globals['render'] = render
web.template.Template.globals['year'] = g_year
