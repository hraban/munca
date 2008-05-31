START TRANSACTION;

CREATE DOMAIN board_t CHAR(2) NOT NULL CHECK (VALUE = 'AB' OR VALUE = 'DB');

CREATE TABLE contact_base (
	contact_id SERIAL PRIMARY KEY,
	contact_addr VARCHAR NOT NULL DEFAULT '',
	contact_comment VARCHAR NOT NULL DEFAULT ''
);

CREATE TABLE country (
	country_id SERIAL PRIMARY KEY,
	country_name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE committee (
	committee_id SERIAL PRIMARY KEY,
	committee_name VARCHAR NOT NULL UNIQUE,
	committee_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE lobby_org (
	lobby_org_id SERIAL PRIMARY KEY,
	lobby_org_name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE entity (
	entity_id INTEGER PRIMARY KEY REFERENCES contact_base ON DELETE CASCADE ON UPDATE CASCADE,
	entity_name VARCHAR NOT NULL UNIQUE
);

-- These entries should not have NULL and '' mixed because this confuses ORDER BY.
CREATE TABLE person (
	person_id INTEGER PRIMARY KEY REFERENCES contact_base ON DELETE CASCADE ON UPDATE CASCADE,
	person_firstname VARCHAR NOT NULL,
	person_surnameprefix VARCHAR NOT NULL,
	person_lastname VARCHAR NOT NULL,
	person_email VARCHAR NOT NULL DEFAULT '',
	person_phonenr VARCHAR NOT NULL DEFAULT '',
	country_id INTEGER REFERENCES country ON UPDATE CASCADE NOT NULL
);

CREATE TABLE contacts (
	contact_person INTEGER REFERENCES person ON DELETE CASCADE ON UPDATE CASCADE,
	contact_target INTEGER REFERENCES contact_base ON DELETE CASCADE ON UPDATE CASCADE,
	PRIMARY KEY (contact_person, contact_target),
	CHECK (contact_person != contact_target)
);

CREATE TABLE participant (
	participant_id INTEGER PRIMARY KEY REFERENCES person ON DELETE CASCADE ON UPDATE CASCADE,
	participant_year INTEGER NOT NULL,
	committee_id INTEGER REFERENCES committee ON UPDATE CASCADE NOT NULL,
	is_chair BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE delegate (
	delegate_id INTEGER PRIMARY KEY REFERENCES participant ON DELETE CASCADE ON UPDATE CASCADE,
	delegate_country INTEGER REFERENCES country ON UPDATE CASCADE NOT NULL
);

CREATE TABLE lobbyist (
	lobbyist_id INTEGER PRIMARY KEY REFERENCES participant ON DELETE CASCADE ON UPDATE CASCADE,
	lobby_org_id INTEGER REFERENCES lobby_org ON UPDATE CASCADE NOT NULL
);

CREATE TABLE boardmember (
	boardmember_id INTEGER PRIMARY KEY REFERENCES person ON DELETE CASCADE ON UPDATE CASCADE,
	board_type board_t, -- board_t does not allow NULL anyway.
	board_start DATE,
	board_stop DATE,
	CHECK (board_start < board_stop)
);

CREATE TABLE double (
	member1 INTEGER REFERENCES boardmember ON DELETE CASCADE ON UPDATE CASCADE,
	member2 INTEGER REFERENCES boardmember ON DELETE CASCADE ON UPDATE CASCADE,
	PRIMARY KEY (member1, member2),
	CHECK (member1 != member2)
);

-- NATURAL JOIN this on "boardmember" for an extra column "board_active", BOOLEAN,
-- indicating whether given boardmember is currently in office.
CREATE VIEW active_bm AS
	SELECT
		boardmember_id,
		((board_start < NOW() OR board_start IS NULL) AND
			(board_stop > NOW() OR board_stop IS NULL))
			AS board_active
	FROM boardmember;

-- Nothing currently prevents delegates and lobbyists from becoming chairs and
-- participants can be none of the above too. Both situations are not wanted
-- but with the current schema the responsibility is with the user to prevent
-- it from happening.
CREATE VIEW type_part AS
	SELECT
		participant_id,
		CASE
			WHEN participant_id IN (SELECT delegate_id FROM delegate)
			THEN 'delegate'
			WHEN participant_id IN (SELECT participant_id FROM participant WHERE is_chair)
			THEN 'chair'
			WHEN participant_id IN (SELECT lobbyist_id FROM lobbyist)
			THEN 'lobbyist'
			END
		AS participant_type
	FROM participant;

COMMIT;
