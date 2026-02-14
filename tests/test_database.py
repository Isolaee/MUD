"""Tests for server.database SQLite data layer."""

import sqlite3

import pytest

import server.database as db
from server.auth import hash_password


@pytest.fixture(autouse=True)
def _use_temp_db(tmp_path, monkeypatch):
	"""Redirect database to a temporary file for test isolation."""
	temp_db = str(tmp_path / "test.db")
	monkeypatch.setattr(db, "DB_PATH", temp_db)
	db.init_db()
	yield


def test_init_db_creates_tables():
	conn = db._connect()
	tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
	table_names = {row["name"] for row in tables}
	assert "accounts" in table_names
	assert "characters" in table_names
	conn.close()


def test_create_and_get_account():
	pw_hash = hash_password("password123")
	account_id = db.create_account("TestUser", pw_hash)
	assert account_id is not None

	row = db.get_account("TestUser")
	assert row is not None
	assert row["username"] == "TestUser"
	assert row["password_hash"] == pw_hash


def test_account_username_case_insensitive():
	db.create_account("Alice", hash_password("pw"))
	row = db.get_account("alice")
	assert row is not None
	assert row["username"] == "Alice"


def test_duplicate_account_raises():
	db.create_account("Bob", hash_password("pw"))
	with pytest.raises(sqlite3.IntegrityError):
		db.create_account("Bob", hash_password("pw2"))


def test_get_nonexistent_account():
	assert db.get_account("nobody") is None


def test_create_and_get_character():
	account_id = db.create_account("Player1", hash_password("pw"))
	char_id = db.create_character_record(account_id, "Thorin", "WARRIOR", "HUMAN", 120, 110, 15)
	assert char_id is not None

	chars = db.get_characters_for_account(account_id)
	assert len(chars) == 1
	assert chars[0]["name"] == "Thorin"
	assert chars[0]["character_class"] == "WARRIOR"


def test_multiple_characters_per_account():
	account_id = db.create_account("Player2", hash_password("pw"))
	db.create_character_record(account_id, "Char1", "MAGE", "HUMAN", 90, 105, 8)
	db.create_character_record(account_id, "Char2", "ROGUE", "HUMAN", 95, 120, 13)

	chars = db.get_characters_for_account(account_id)
	assert len(chars) == 2


def test_duplicate_character_name_same_account_raises():
	account_id = db.create_account("Player3", hash_password("pw"))
	db.create_character_record(account_id, "Dupe", "WARRIOR", "HUMAN", 100, 100, 10)
	with pytest.raises(sqlite3.IntegrityError):
		db.create_character_record(account_id, "Dupe", "MAGE", "HUMAN", 90, 105, 8)


def test_same_character_name_different_accounts():
	a1 = db.create_account("P1", hash_password("pw"))
	a2 = db.create_account("P2", hash_password("pw"))
	db.create_character_record(a1, "Hero", "WARRIOR", "HUMAN", 100, 100, 10)
	db.create_character_record(a2, "Hero", "WARRIOR", "HUMAN", 100, 100, 10)
	assert len(db.get_characters_for_account(a1)) == 1
	assert len(db.get_characters_for_account(a2)) == 1


def test_save_character():
	account_id = db.create_account("Saver", hash_password("pw"))
	char_id = db.create_character_record(account_id, "Tank", "WARRIOR", "HUMAN", 120, 110, 15)
	db.save_character(char_id, hp=50, stamina=30)

	row = db.get_character_by_id(char_id)
	assert row["hp"] == 50
	assert row["stamina"] == 30


def test_load_player_character():
	account_id = db.create_account("Loader", hash_password("pw"))
	char_id = db.create_character_record(account_id, "Gandalf", "MAGE", "HUMAN", 90, 105, 8)
	row = db.get_character_by_id(char_id)
	player = db.load_player_character(row)

	assert player.name == "Gandalf"
	assert player.hp == 90
	assert player.stamina == 105
	assert player.base_attack == 8
	assert player.character_class.name == "MAGE"
	assert player.race.name == "HUMAN"
