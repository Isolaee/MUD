"""SQLite data layer for account and character persistence.

All functions open and close their own connection, which is safe for
the single-threaded asyncio event loop used by the SSH server.
"""

from __future__ import annotations

import os
import sqlite3

from Objects.Characters.character import (
	CharacterClassOptions,
	CharacterRaceOptions,
	PlayerCharacter,
)
from Objects.Characters.characterRaces import get_all_races

DB_PATH = os.path.join(os.path.dirname(__file__), "mud.db")

_SCHEMA = """\
CREATE TABLE IF NOT EXISTS accounts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS characters (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id      INTEGER NOT NULL REFERENCES accounts(id),
    name            TEXT    NOT NULL,
    character_class TEXT    NOT NULL,
    character_race  TEXT    NOT NULL DEFAULT 'HUMAN',
    hp              INTEGER NOT NULL DEFAULT 100,
    stamina         INTEGER NOT NULL DEFAULT 100,
    base_attack     INTEGER NOT NULL DEFAULT 10,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(account_id, name)
);
"""


def _connect() -> sqlite3.Connection:
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	conn.execute("PRAGMA foreign_keys = ON")
	return conn


def init_db() -> None:
	"""Create tables if they don't already exist."""
	conn = _connect()
	conn.executescript(_SCHEMA)
	conn.close()


# -- accounts ----------------------------------------------------------------


def create_account(username: str, password_hash: str) -> int:
	"""Insert a new account. Returns the new account id.

	Raises sqlite3.IntegrityError if the username is taken.
	"""
	conn = _connect()
	try:
		cur = conn.execute(
			"INSERT INTO accounts (username, password_hash) VALUES (?, ?)",
			(username, password_hash),
		)
		conn.commit()
		return cur.lastrowid
	finally:
		conn.close()


def get_account(username: str) -> sqlite3.Row | None:
	"""Fetch an account row by username, or None."""
	conn = _connect()
	try:
		row = conn.execute("SELECT * FROM accounts WHERE username = ?", (username,)).fetchone()
		return row
	finally:
		conn.close()


# -- characters --------------------------------------------------------------


def create_character_record(
	account_id: int,
	name: str,
	character_class: str,
	character_race: str,
	hp: int,
	stamina: int,
	base_attack: int,
) -> int:
	"""Insert a new character. Returns the character id.

	Raises sqlite3.IntegrityError if (account_id, name) already exists.
	"""
	conn = _connect()
	try:
		cur = conn.execute(
			"INSERT INTO characters "
			"(account_id, name, character_class, character_race, hp, stamina, base_attack) "
			"VALUES (?, ?, ?, ?, ?, ?, ?)",
			(account_id, name, character_class, character_race, hp, stamina, base_attack),
		)
		conn.commit()
		return cur.lastrowid
	finally:
		conn.close()


def get_characters_for_account(account_id: int) -> list[sqlite3.Row]:
	"""Return all character rows belonging to an account."""
	conn = _connect()
	try:
		rows = conn.execute(
			"SELECT * FROM characters WHERE account_id = ? ORDER BY created_at",
			(account_id,),
		).fetchall()
		return rows
	finally:
		conn.close()


def get_character_by_id(character_id: int) -> sqlite3.Row | None:
	"""Fetch a single character row by id."""
	conn = _connect()
	try:
		return conn.execute("SELECT * FROM characters WHERE id = ?", (character_id,)).fetchone()
	finally:
		conn.close()


def save_character(character_id: int, hp: int, stamina: int) -> None:
	"""Persist mutable character stats (called on disconnect / save)."""
	conn = _connect()
	try:
		conn.execute(
			"UPDATE characters SET hp = ?, stamina = ? WHERE id = ?",
			(hp, stamina, character_id),
		)
		conn.commit()
	finally:
		conn.close()


def load_player_character(char_row: sqlite3.Row) -> PlayerCharacter:
	"""Reconstruct a PlayerCharacter from a database row."""
	race = CharacterRaceOptions[char_row["character_race"]]
	char_class = CharacterClassOptions[char_row["character_class"]]
	race_instance = get_all_races()[race.name]()

	return PlayerCharacter(
		current_hp=char_row["hp"],
		current_stamina=char_row["stamina"],
		base_attack=char_row["base_attack"],
		race=race,
		character_class=char_class,
		characterSize=race_instance.size,
		inventory=[],
		name=char_row["name"],
	)
