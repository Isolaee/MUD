"""Tests for character creation, stats, classes, and races."""

from Objects.Characters.character import (
	CharacterClassOptions,
	CharacterRaceOptions,
	CharacterType,
	PlayerCharacter,
	NonPlayerCharacter,
)
from Objects.Characters.characterClasses import (
	Warrior,
	Mage,
	Rogue,
	Cleric,
	get_all_classes,
)
from Objects.Characters.characterRaces import CharacterSize, get_all_races
from Objects.Rooms.room import Room


def _make_player(name="Hero", cls=CharacterClassOptions.WARRIOR):
	return PlayerCharacter(
		current_hp=100,
		current_stamina=100,
		base_attack=10,
		race=CharacterRaceOptions.HUMAN,
		character_class=cls,
		characterSize=CharacterSize.MEDIUM,
		inventory=[],
		name=name,
	)


class TestCharacterClasses:
	def test_get_all_classes_returns_four(self):
		classes = get_all_classes()
		assert set(classes.keys()) == {"WARRIOR", "MAGE", "ROGUE", "CLERIC"}

	def test_warrior_stat_modifiers(self):
		w = Warrior()
		assert w.stat_modifiers.hp == 20
		assert w.stat_modifiers.stamina == 10
		assert w.stat_modifiers.attack == 5

	def test_mage_stat_modifiers(self):
		m = Mage()
		assert m.stat_modifiers.hp == -10
		assert m.stat_modifiers.attack == -2

	def test_rogue_stat_modifiers(self):
		r = Rogue()
		assert r.stat_modifiers.stamina == 20

	def test_cleric_stat_modifiers(self):
		c = Cleric()
		assert c.stat_modifiers.attack == 0
		assert c.stat_modifiers.hp == 10

	def test_class_name_property(self):
		assert Warrior().className == "Warrior"
		assert Mage().className == "Mage"


class TestCharacterRaces:
	def test_get_all_races_includes_human(self):
		races = get_all_races()
		assert "HUMAN" in races

	def test_human_no_stat_modifiers(self):
		human = get_all_races()["HUMAN"]()
		mods = human.stat_modifiers
		assert mods.hp == 0
		assert mods.stamina == 0
		assert mods.attack == 0


class TestPlayerCharacter:
	def test_basic_stats(self):
		pc = _make_player()
		assert pc.hp == 100
		assert pc.stamina == 100
		assert pc.base_attack == 10

	def test_object_type(self):
		pc = _make_player()
		assert pc.object_type() == CharacterType.PLAYER

	def test_inventory_starts_empty(self):
		pc = _make_player()
		assert pc.inventory == []

	def test_visit_room(self):
		pc = _make_player()
		room = Room("Tavern")
		assert not pc.has_visited(room)
		pc.visit_room(room)
		assert pc.has_visited(room)

	def test_visit_room_idempotent(self):
		pc = _make_player()
		room = Room("Tavern")
		pc.visit_room(room)
		pc.visit_room(room)
		assert len(pc.visited_rooms) == 1

	def test_create_character_applies_class_modifiers(self):
		pc = _make_player()
		warrior = pc.create_character("Tank", CharacterRaceOptions.HUMAN, CharacterClassOptions.WARRIOR)
		# Warrior: hp+20, stamina+10, attack+5 on base 100/100/10
		assert warrior.hp == 120
		assert warrior.stamina == 110
		assert warrior.base_attack == 15

	def test_create_character_mage_modifiers(self):
		pc = _make_player()
		mage = pc.create_character("Gandalf", CharacterRaceOptions.HUMAN, CharacterClassOptions.MAGE)
		# Mage: hp-10, stamina+5, attack-2
		assert mage.hp == 90
		assert mage.stamina == 105
		assert mage.base_attack == 8


class TestNonPlayerCharacter:
	def test_npc_object_type(self):
		npc = NonPlayerCharacter(
			has_enters_the_room=False,
			current_hp=50,
			current_stamina=50,
			base_attack=5,
			race=CharacterRaceOptions.HUMAN,
			character_class=CharacterClassOptions.CLERIC,
			characterSize=CharacterSize.MEDIUM,
			inventory=[],
			name="Shopkeeper",
		)
		assert npc.object_type() == CharacterType.NPC

	def test_npc_quest_default_none(self):
		npc = NonPlayerCharacter(
			has_enters_the_room=True,
			current_hp=50,
			current_stamina=50,
			base_attack=5,
			race=CharacterRaceOptions.HUMAN,
			character_class=CharacterClassOptions.WARRIOR,
			characterSize=CharacterSize.MEDIUM,
			inventory=[],
			name="Guard",
		)
		assert npc.quest is None
