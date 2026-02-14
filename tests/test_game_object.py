"""Tests for Objects.game_object base class."""

from Objects.Rooms.room import Room


class TestGameObjectProperties:
	"""Property store on GameObject (tested via Room, a concrete subclass)."""

	def test_set_and_get_property(self):
		obj = Room("TestRoom")
		obj.set_prop("level", 5)
		assert obj.get_prop("level") == 5

	def test_get_missing_property_returns_default(self):
		obj = Room("TestRoom")
		assert obj.get_prop("missing") is None
		assert obj.get_prop("missing", 42) == 42

	def test_has_prop(self):
		obj = Room("TestRoom")
		assert not obj.has_prop("key")
		obj.set_prop("key", "value")
		assert obj.has_prop("key")

	def test_remove_prop(self):
		obj = Room("TestRoom")
		obj.set_prop("temp", True)
		obj.remove_prop("temp")
		assert not obj.has_prop("temp")

	def test_remove_absent_prop_no_error(self):
		obj = Room("TestRoom")
		obj.remove_prop("nonexistent")  # should not raise


class TestGameObjectTags:
	"""Tag system on GameObject."""

	def test_add_and_has_tag(self):
		obj = Room("TestRoom")
		assert not obj.has_tag("safe_zone")
		obj.add_tag("safe_zone")
		assert obj.has_tag("safe_zone")

	def test_remove_tag(self):
		obj = Room("TestRoom")
		obj.add_tag("dungeon")
		obj.remove_tag("dungeon")
		assert not obj.has_tag("dungeon")

	def test_remove_absent_tag_no_error(self):
		obj = Room("TestRoom")
		obj.remove_tag("nonexistent")  # should not raise

	def test_multiple_tags(self):
		obj = Room("TestRoom")
		obj.add_tag("indoor")
		obj.add_tag("lit")
		assert obj.has_tag("indoor")
		assert obj.has_tag("lit")
		assert not obj.has_tag("outdoor")


class TestGameObjectIdentity:
	"""UID-based equality and hashing."""

	def test_unique_uids(self):
		a = Room("A")
		b = Room("B")
		assert a.uid != b.uid

	def test_equality_by_uid(self):
		a = Room("A")
		b = Room("B")
		assert a != b
		# Force same UID to test equality
		b.uid = a.uid
		assert a == b

	def test_hash_matches_uid(self):
		obj = Room("R")
		assert hash(obj) == hash(obj.uid)

	def test_usable_in_set(self):
		rooms = {Room("A"), Room("B"), Room("C")}
		assert len(rooms) == 3

	def test_repr_contains_name(self):
		obj = Room("Tavern")
		assert "Tavern" in repr(obj)
		assert "Room" in repr(obj)
