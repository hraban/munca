import web

from project import *

urls = (
        '/boardmember/add','add.add_boardmem',
        '/committee/add',  'add.add_committee',
        '/country/add',    'add.add_country',
        '/delegate/add',   'add.add_delegate',
        '/entity/add',     'add.add_entity',
        '/lobbyist/add',   'add.add_lobbyist',
        '/lobby_org/add',  'add.add_lobby_org',
        '/person/add',     'add.add_person',
        )

def _add_participant(i):
    """Add a new participant.
    
    Returns the id of the new participant. IMPORTANT: ONLY RUN THIS FUNCTION
    FROM WITHIN A TRANSACTION BLOCK!
    
    """
    new_id = _add_person(i)
    db.insert("participant",
            participant_id=new_id,
            participant_year=i.year,
            committee_id=i.committee,
            seqname=False
            )
    return new_id

def _add_person(i):
    """Add a person to the database.
    
    IMPORTANT: ONLY RUN THIS FUNCTION FROM WITHIN A TRANSACTION BLOCK!
    
    """
    # Add a new base contact.
    new_id = db.insert("contact_base",
            seqname="contact_base_contact_id_seq")
    db.insert("person",
            person_id=new_id,
            person_firstname=i.firstname,
            person_surnameprefix=i.surnameprefix,
            person_lastname=i.lastname,
            person_email=i.email,
            country_id=i.origin,
            seqname=False
            )
    return new_id

class add_boardmem:
    def POST(self):
        i = web.input(active="FALSE")
        t = db.transaction()
        new_id = _add_person(i)
        db.insert("boardmember",
                boardmember_id=new_id,
                board_start=i.start,
                board_type=i.type,
                seqname=False
                )
        t.commit()
        web.seeother("/boardmember/%d" % new_id)

class add_committee:
    def POST(self):
        i = web.input()
        new_id = db.insert("committee", committee_name=i.name,
                seqname="committee_committee_id_seq")
        web.seeother("/committee/%d" % new_id)

class add_country:
    def POST(self):
        i = web.input()
        db.insert("country", country_name=i.name, seqname=False)
        web.seeother("/country/")

class add_delegate:
    def POST(self):
        i = web.input()
        t = db.transaction()
        new_id = _add_participant(i)
        db.insert("delegate", delegate_id=new_id,
                delegate_country=i.repr_country, seqname=False)
        t.commit()
        web.seeother("/country/%s" % i.repr_country)

class add_entity:
    def POST(self):
        i = web.input()
        t = db.transaction()
        # Add a new base contact.
        new_id = db.insert("contact_base",
                seqname="contact_base_contact_id_seq")
        db.insert("entity",
                entity_name=i.name,
                entity_id=new_id,
                seqname=False
                )
        t.commit()
        web.seeother("/entity/%d" % new_id)

class add_lobbyist:
    def POST(self):
        i = web.input()
        t = db.transaction()
        new_id = _add_participant(i)
        db.insert("lobbyist", lobbyist_id=new_id, lobby_org_id=i.lobbies_for,
                seqname=False)
        t.commit()
        web.seeother("/lobby_org/%s" % i.lobbies_for)

class add_lobby_org:
    def POST(self):
        i = web.input()
        new_id = db.insert("lobby_org", lobby_org_name=i.name,
                seqname="lobby_org_lobby_org_id_seq")
        web.seeother("/lobby_org/%d" % new_id)

class add_person:
    def POST(self):
        t = db.transaction()
        web.seeother("/person/%d" % _add_person(web.input()))
        t.commit()
