import web

from project import *

urls = (
        '/boardmember/(\d+)','detail.detail_boardmem',
        '/committee/(\d+)',  'detail.detail_committee',
        '/country/(\d+)',    'detail.detail_country',
        '/entity/(\d+)',     'detail.detail_entity',
        '/lobby_org/(\d+)',  'detail.detail_lobby_org',
        '/participant/(\d+)','detail.detail_participant',
        '/person/(\d+)',     'detail.detail_person',
        )

class detail_boardmem:
    def GET(self, mem_id):
        mem = db.select("""boardmember NATURAL JOIN active_bm INNER JOIN person
                ON boardmember_id = person_id NATURAL JOIN country""",
                where="boardmember_id = $mem_id", vars=locals())[0]
        if web.input(action=None).action == "edit":
            return render.edit_boardmem(mem)
        else:
            doubles = db.select("""boardmember INNER JOIN person ON
                    boardmember_id = person_id""", what="""*, boardmember_id IN
                    ( SELECT member1 FROM double WHERE member2 = $mem_id
                    UNION
                      SELECT member2 FROM double WHERE member1 = $mem_id )
                    AS is_double""", vars=locals())
            return render.info_boardmem(mem, tuple(doubles))

    def POST(self, mem_id):
        """Update an entry in the person table."""
        i = web.input("action")
        if i.action == "delete":
            return del_contact(mem_id)
        elif i.action == "update":
            db.update("boardmember", where="boardmember_id = $mem_id",
                    board_start=i.start or None, # Map empty string to NULL
                    board_stop=i.stop or None,
                    vars=locals())
            web.seeother("/boardmember/%s" % mem_id)
        elif i.action == "add double":
            db.insert("double", member1=mem_id, member2=i.double,
                    seqname=False)
            web.seeother("/boardmember/%s" % mem_id)
        elif i.action == "delete double":
            db.delete("double", where="""
                    (member1 = $i.double AND member2 = $mem_id) OR
                    (member2 = $i.double AND member1 = $mem_id)""",
                    vars=locals())
            web.seeother("/boardmember/%s" % mem_id)

class detail_committee:
    def GET(self, c_id):
        c = db.select("committee", where="committee_id = $c_id",
                vars=locals())[0]
        chairs = db.select("""participant INNER JOIN person ON participant_id =
                person_id""", where="""committee_id = $id AND participant_year
                = $year AND is_chair""", vars=dict(id=c_id, year=g_year))
        parts_other_years = db.select("""participant INNER JOIN person ON
                participant_id = person_id""", vars=dict(id=c_id, year=g_year),
                where="committee_id = $id AND participant_year != $year")
        parts_this_year = db.select("""participant INNER JOIN person ON
                participant_id = person_id""", vars=dict(id=c_id, year=g_year),
                where="committee_id = $id AND participant_year = $year")
        return render.info_committee(c, chairs, parts_this_year, parts_other_years,
                len(parts_this_year))

    def POST(self, c_id):
        if web.input("action").action == "delete":
            db.delete("committee", where="committee_id = $c_id",
                    vars=locals())
            return "Committee %s succesfully deleted." % c_id

class detail_country:
    def GET(self, c_id):
        c = db.select("country", where="country_id = $c_id",
                vars=locals())[0]
        people = db.select("person", where="country_id = $c_id",
                vars=locals())
        delegates = db.select("""delegate INNER JOIN participant ON delegate_id
                = participant_id INNER JOIN person ON participant_id =
                person_id""", where="delegate_country = $c_id",
                order="participant_year DESC", vars=locals())
        return render.info_country(c, people, len(people), delegates,
                len(delegates))

    def POST(self, c_id):
        if web.input("action").action == "delete":
            db.delete("country", where="country_id = $c_id",
                    vars=locals())
            return "Country %s succesfully deleted." % c_id

class detail_entity:
    def GET(self, ent_id):
        i = web.input(action=None)
        entity = db.select("""entity INNER JOIN contact_base ON entity_id
            = contact_id""", where="entity_id = $ent_id", vars=locals())[0]
        if i.action == "edit":
            contacts = db.select("person", what="""*, person_id IN (SELECT
                    contact_person FROM contacts WHERE contact_target =
                    $ent_id) AS is_contact_for_me""", order="person_lastname",
                    vars=locals())
            return render.edit_entity(entity, contacts)
        else:
            # People this entity should be contacted through.
            contacts_for_me = db.select("person", where="""person_id IN (SELECT
                    contact_person FROM contacts WHERE contact_target =
                    $ent_id)""", vars=locals())
            return render.info_entity(entity, contacts_for_me)

    def POST(self, ent_id):
        """Update an entry in the entry table."""
        i = web.input("action", contact_person=[])
        if i.action == "update":
            old_cs = db.select("contacts", what="contact_person",
                    where="contact_target = $ent_id", vars=locals())
            # Extract the person_ids.
            old_cs = set((c.contact_person for c in old_cs))
            new_cs = set(i.contact_person)
            t = db.transaction()
            db.update("contact_base", where="contact_id = $ent_id",
                    contact_comment=i.comment,
                    contact_addr=i.address,
                    vars=locals()
                    )
            db.update("entity", where="entity_id = $ent_id",
                    entity_name=i.name, vars=locals())
            # Old contacts that have been removed.
            for c in old_cs - new_cs:
                db.delete("contacts", where="""contact_target = $ent_id AND
                        contact_person = $c""", vars=locals())
            # New contacts that have been added.
            for c in new_cs - old_cs:
                db.insert("contacts", contact_target=ent_id, contact_person=c,
                        seqname=False)
            t.commit()
            web.seeother("/entity/%s" % ent_id)
        elif i.action == "delete":
            db.delete("contact_base", where="contact_id = $ent_id",
                    vars=locals())
            return "Entity %s succesfully deleted." % ent_id

class detail_lobby_org:
    def GET(self, l_id):
        org = db.select("lobby_org", where="lobby_org_id = $l_id",
                vars=locals())[0]
        lobbyists_this_y = db.select("""lobbyist INNER JOIN participant ON
                lobbyist_id = participant_id INNER JOIN person ON
                participant_id = person_id""", where="""lobby_org_id = $id
                AND participant_year = $y""", vars=dict(id=l_id, y=g_year))
        lobbyists_other_y = db.select("""lobbyist INNER JOIN participant ON
                lobbyist_id = participant_id INNER JOIN person ON
                participant_id = person_id""", where="""lobby_org_id = $id
                AND participant_year != $y""", vars=dict(id=l_id, y=g_year))
        return render.info_lobby_org(org, lobbyists_this_y, lobbyists_other_y,
                len(lobbyists_this_y))

    def POST(self, l_id):
        i = web.input("action")
        if i.action == "delete":
            db.delete("lobby_org", where="lobby_org_id = $l_id", vars=locals())
            return "Succesfully deleted organisation #%s" % l_id
        elif i.action == "update":
            db.update("lobby_org", where="lobby_org_id = $l_id", vars=locals(),
                    lobby_org_name=i.name)
            web.seeother("/lobby_org/%s" % l_id)

class detail_participant:
    def GET(self, p_id):
        i = web.input(action=None)
        participant = db.select("""participant NATURAL JOIN type_part NATURAL
                JOIN committee INNER JOIN person ON participant_id = person_id
                NATURAL JOIN country INNER JOIN contact_base ON person_id =
                contact_id""", where="""person_id = $p_id""", vars=locals())[0]
        if i.action == "edit":
            return render.edit_participant(participant, db.select("committee"))
        else:
            return render.info_participant(participant)

    def POST(self, p_id):
        i = web.input("action")
        if i.action == "delete":
            return del_contact(p_id)
        elif i.action == "update":
            db.update("participant", where="participant_id = $p_id",
                    participant_year=i.year,
                    committee_id=i.committee,
                    vars=locals()
                    )
            web.seeother("/participant/%s" % p_id)
        elif i.action == "make chair":
            db.update("participant", "participant_id = $p_id", is_chair=True,
                    vars=locals())
            return "Succesfully made chair of his/her committee."
        elif i.action == "unset chair":
            db.update("participant", "participant_id = $p_id", is_chair=False,
                    vars=locals())
            return "Succesfully removed from the position of chair."

class detail_person:
    def GET(self, p_id):
        i = web.input(action=None)
        person = db.select("""person NATURAL JOIN country INNER JOIN
                contact_base ON person_id = contact_id""", what="""*, person_id
                IN (SELECT participant_id FROM participant) AS
                is_participant""", where="person_id = $p_id", vars=locals())[0]
        if i.action == "edit":
            contacts = db.select("person", what="""*, person_id IN (SELECT
                    contact_person FROM contacts WHERE contact_target = $p_id)
                    AS is_contact_for_me""", order="person_lastname",
                    where="person_id != $p_id", vars=locals())
            countries = db.select("country", order="country_name")
            return render.edit_person(person, countries, contacts)
        else:
            # Everything this guy is a contact-person for: ...
            my_contacts = []
            # ... people ...
            for c in db.select("person", what="*, person_id AS contact_id",
                    where="""person_id IN (SELECT contact_target FROM contacts
                    WHERE contact_person = $p_id)""", vars=locals()):
                c.type = "person"
                c.text = p_name(c)
                my_contacts.append(c)
            # ... and entities.
            for c in db.select("entity", what="*, entity_id AS contact_id",
                    where="""entity_id IN (SELECT contact_target FROM contacts
                    WHERE contact_person = $p_id)""", vars=locals()):
                c.type = "entity"
                c.text = c.entity_name
                my_contacts.append(c)
            # People this person should be contact through.
            contacts_for_me = db.select("person", where="""person_id IN (SELECT
                    contact_person FROM contacts WHERE contact_target =
                    $p_id)""", vars=locals())
            return render.info_person(person, my_contacts, contacts_for_me)

    def POST(self, p_id):
        """Update an entry in the person table."""
        i = web.input("action", contact_person=[])
        if i.action == "update":
            old_cs = db.select("contacts", what="contact_person",
                    where="contact_target = $p_id", vars=locals())
            # Extract the person_ids.
            old_cs = set((c.contact_person for c in old_cs))
            new_cs = set(i.contact_person)
            t = db.transaction()
            db.update("contact_base", where="contact_id = $p_id",
                    contact_comment=i.comment,
                    contact_addr=i.address,
                    vars=locals()
                    )
            db.update("person", where="person_id = $p_id",
                    person_firstname=i.firstname,
                    person_surnameprefix=i.surnameprefix,
                    person_lastname=i.lastname,
                    person_email=i.email,
                    person_phonenr=i.phonenr,
                    country_id=i.country,
                    vars=locals()
                    )
            # Old contacts that have been removed.
            for c in old_cs - new_cs:
                db.delete("contacts", where="""contact_target = $p_id AND
                        contact_person = $c""", vars=locals())
            # New contacts that have been added.
            for c in new_cs - old_cs:
                db.insert("contacts", contact_target=p_id, contact_person=c,
                        seqname=False)
            t.commit()
            web.seeother("/person/%s" % p_id)
        elif i.action == "delete contact target":
            db.delete("contacts", where="""contact_person = $p_id AND
                    contact_target = $i.contact_target""", vars=locals())
            web.seeother("/person/%s" % p_id)
        elif i.action == "delete":
            return del_contact(p_id)
