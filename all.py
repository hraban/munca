"""Hooks for showing everything about a certain entity or relation."""

import web

from project import *

urls = (
        '/',               'all.all',
        '/all',            'all.redir_home',
        '/boardmember/',   'all.all_boardmems',
        '/committee/',     'all.all_committees',
        '/country/',       'all.all_countries',
        '/participant/',   'all.all_participants',
        '/person/',        'all.all_people',
        )

class redir_home:
    def GET(self):
        web.redirect("/")

class all:
    def GET(self):
        boardmems = db.select("""boardmember NATURAL JOIN active_bm INNER JOIN
                person ON boardmember_id = person_id""", where="board_active",
                order="person_lastname")
        chairs = db.select("""participant NATURAL JOIN committee INNER JOIN
                person ON participant_id = person_id""", where="""is_chair AND
                participant_year = $g_year""", order="committee_name",
                vars=globals())
        committees = tuple(db.select("committee", what="""*, (SELECT COUNT(*)
                FROM participant WHERE participant.committee_id =
                committee.committee_id AND participant_year = $g_year) AS
                num_participants""", order="committee_name", vars=globals()))
        countries = tuple(db.select("country", order="country_name"))
        entities = db.select("entity", order="entity_name")
        lobby_orgs = tuple(db.select("lobby_org", what="""*, (SELECT COUNT(*)
                FROM lobbyist WHERE lobbyist.lobby_org_id =
                lobby_org.lobby_org_id) AS num_lobbyists"""))
        participants = db.select("""participant INNER JOIN person ON
                participant_id = person_id NATURAL JOIN country WHERE
                participant_year = $g_year""", vars=globals(),
                order="person_lastname")
        people = db.select("person", order="person_id DESC", limit=10)
        return render.all(boardmems, chairs, committees, countries, entities,
                lobby_orgs, participants, people)

class all_boardmems:
    """View a list of all boardmembers in the DB."""
    def GET(self):
        i = web.input(sort="board_active", order="desc")
        check_table_sort(i)
        mems = db.select("""boardmember NATURAL JOIN active_bm INNER JOIN
                person ON boardmember_id = person_id """, order="%s %s" %
                (i.sort, i.order))
        countries = db.select("country", order="country_name")
        return render.all_boardmems(mems, countries)

class all_committees:
    def GET(self):
        i = web.input(sort="committee_active", order="desc")
        check_table_sort(i)
        committees = db.select("committee", what="""
                *,
                (SELECT COUNT(*)
                    FROM delegate INNER JOIN
                        participant ON delegate_id = participant_id
                    WHERE committee.committee_id = participant.committee_id AND
                        participant_year = $g_year
                    ) AS num_delegates_this_year,
                (SELECT COUNT(*)
                    FROM delegate INNER JOIN
                        participant ON delegate_id = participant_id
                    WHERE committee.committee_id = participant.committee_id AND
                        participant_year != $g_year
                    ) AS num_delegates_other_years,
                (SELECT COUNT(*)
                    FROM lobbyist INNER JOIN
                        participant ON lobbyist_id = participant_id
                    WHERE committee.committee_id = participant.committee_id AND
                        participant_year = $g_year
                    ) AS num_lobbyists_this_year,
                (SELECT COUNT(*)
                    FROM lobbyist INNER JOIN
                        participant ON lobbyist_id = participant_id
                    WHERE committee.committee_id = participant.committee_id AND
                        participant_year != $g_year
                    ) AS num_lobbyists_other_years,
                (SELECT COUNT(*)
                    FROM (SELECT DISTINCT delegate_country FROM delegate
                        INNER JOIN
                        participant ON delegate_id = participant_id
                    WHERE committee.committee_id = participant.committee_id AND
                        participant_year = $g_year
                    GROUP BY delegate_country
                    ) AS foo1) AS num_countries_this_year,
                (SELECT COUNT(*)
                    FROM (SELECT DISTINCT delegate_country FROM delegate
                        INNER JOIN
                        participant ON delegate_id = participant_id
                    WHERE committee.committee_id = participant.committee_id AND
                        participant_year = $g_year
                    GROUP BY delegate_country
                    ) AS foo2) AS num_countries_other_years""", vars=globals(),
                order="%s %s" % (i.sort, i.order))
        return render.all_committees(committees, len(committees))

class all_countries:
    def GET(self):
        i = web.input(sort="country_name", order="asc")
        check_table_sort(i)
        countries = db.select("country", what="""*, (SELECT COUNT(*) FROM
                delegate WHERE delegate_country = country_id) AS num_delegates,
                (SELECT COUNT(*) FROM person WHERE person.country_id =
                country.country_id) AS num_inhabitants""", order="%s %s" %
                (i.sort, i.order))
        return render.all_countries(countries, len(countries))

class all_participants:
    def GET(self):
        i = web.input(sort="participant_year", order="desc")
        check_table_sort(i)
        committees = tuple(db.select("committee", what="""*, (SELECT COUNT(*)
                FROM participant WHERE participant.committee_id =
                committee.committee_id AND participant_year = $g_year) AS
                num_participants""", order="committee_name", vars=globals()))
        countries = tuple(db.select("country", order="country_name"))
        participants = tuple(db.select("""participant NATURAL JOIN committee
                INNER JOIN person ON participant_id = person_id NATURAL JOIN
                country INNER JOIN contact_base ON contact_id = person_id""",
                order="%(sort)s %(order)s" % i))
        for p in participants:
            if p.contact_comment:
                txt = p.contact_comment.decode("utf-8")
                if len(txt) > 49:
                    txt = txt[:49] + u"\u2026" # \u2026 is three dots: ...
                p.shortcomment = txt.encode("utf-8")
            else:
                p.shortcomment = None
        return render.all_participants(participants, len(participants),
                committees, countries)

class all_people:
    """View a list of all people in the DB."""
    def GET(self):
        i = web.input(sort="person_lastname", order="asc")
        check_table_sort(i)
        people = tuple(db.select("""person NATURAL JOIN country INNER JOIN
            contact_base ON contact_id = person_id""",
            order="%(sort)s %(order)s" % i))
        countries = db.select("country", order="country_name")
        for p in people:
            if p.contact_comment and len(p.contact_comment) > 49:
                p.shortcomment = p.contact_comment[:49] + u"\u2026"
            else:
                p.shortcomment = p.contact_comment
        return render.all_people(people, len(people), countries)
