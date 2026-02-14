"""Tests for Objects.Rooms.room — Room, Direction, Description."""

import pytest

from Objects.Rooms.room import Description, Direction, OPPOSITE, Room


class TestDescription:
	def test_short_and_long(self):
		desc = Description("A dark cave", "The walls drip with moisture.")
		assert desc.short == "A dark cave"
		assert desc.long == "The walls drip with moisture."

	def test_long_defaults_empty(self):
		desc = Description("A field")
		assert desc.long == ""


class TestDirection:
	def test_all_eight_directions_exist(self):
		assert len(Direction) == 8

	def test_opposite_mapping_is_symmetric(self):
		for d, opp in OPPOSITE.items():
			assert OPPOSITE[opp] == d


class TestRoomConnections:
	def test_add_connection_bidirectional(self):
		a = Room("A")
		b = Room("B")
		a.add_connection(b, Direction.NORTH)
		assert a.connected_rooms[Direction.NORTH] is b
		assert b.connected_rooms[Direction.SOUTH] is a

	def test_add_connection_rejects_duplicate_direction(self):
		a = Room("A")
		b = Room("B")
		c = Room("C")
		a.add_connection(b, Direction.EAST)
		with pytest.raises(ValueError):
			a.add_connection(c, Direction.EAST)

	def test_add_connection_rejects_reverse_conflict(self):
		a = Room("A")
		b = Room("B")
		c = Room("C")
		# B already has WEST occupied via a->b EAST
		a.add_connection(b, Direction.EAST)
		with pytest.raises(ValueError):
			c.add_connection(b, Direction.EAST)

	def test_multiple_connections(self):
		center = Room("Center")
		north = Room("North")
		east = Room("East")
		center.add_connection(north, Direction.NORTH)
		center.add_connection(east, Direction.EAST)
		assert len(center.connected_rooms) == 2


class TestRoomOccupants:
	def test_add_item(self):
		from Objects.Items.Swords.shortSword import ShortSword

		room = Room("Armory")
		sword = ShortSword(
			reach=1,
			name="Short Sword",
			durability=100,
			degrades=True,
			attackBonus=2,
			onHitEffect=[],
		)
		room.add_item(sword)
		assert sword in room.present_items

	def test_add_character(self):
		from Objects.Characters.character import (
			CharacterClassOptions,
			CharacterRaceOptions,
			NonPlayerCharacter,
		)
		from Objects.Characters.characterRaces import CharacterSize

		room = Room("Town Square")
		npc = NonPlayerCharacter(
			has_enters_the_room=False,
			current_hp=100,
			current_stamina=100,
			base_attack=5,
			race=CharacterRaceOptions.HUMAN,
			character_class=CharacterClassOptions.CLERIC,
			characterSize=CharacterSize.MEDIUM,
			inventory=[],
			name="Merchant",
		)
		room.add_character(npc)
		assert npc in room.present_characters
