"""Tests for logic.actions — command parsing and execution."""

from Objects.Characters.character import (
	CharacterClassOptions,
	CharacterRaceOptions,
	NonPlayerCharacter,
)
from Objects.Characters.characterRaces import CharacterSize
from Objects.Items.Swords.shortSword import ShortSword
from Objects.Rooms.room import Description, Direction, Room
from logic.actions import Action, parse, execute


def _make_world():
	"""Create two connected rooms with an item and NPC."""
	tavern = Room("Tavern")
	tavern.description = Description("A cozy tavern", "A warm fire crackles in the hearth.")

	market = Room("Market")
	market.description = Description("Town market", "Stalls line the busy square.")

	tavern.add_connection(market, Direction.EAST)

	sword = ShortSword(
		reach=1,
		name="Short Sword",
		durability=100,
		degrades=True,
		attackBonus=2,
		onHitEffect=[],
	)
	tavern.add_item(sword)

	npc = NonPlayerCharacter(
		has_enters_the_room=False,
		current_hp=50,
		current_stamina=50,
		base_attack=5,
		race=CharacterRaceOptions.HUMAN,
		character_class=CharacterClassOptions.CLERIC,
		characterSize=CharacterSize.MEDIUM,
		inventory=[],
		name="Barkeep",
	)
	tavern.add_character(npc)

	return tavern, market, sword, npc


# -- Parse tests --


class TestParse:
	def test_empty_input_defaults_to_look(self):
		room = Room("R")
		action, inputs = parse("", room)
		assert action == Action.LOOK
		assert inputs[0] is room

	def test_look_command(self):
		room = Room("R")
		action, inputs = parse("look", room)
		assert action == Action.LOOK

	def test_look_alias(self):
		room = Room("R")
		action, _ = parse("l", room)
		assert action == Action.LOOK

	def test_move_command(self):
		tavern, market, _, _ = _make_world()
		action, inputs = parse("move market", tavern)
		assert action == Action.MOVE
		assert inputs[0] is market

	def test_move_alias_mv(self):
		tavern, market, _, _ = _make_world()
		action, inputs = parse("mv market", tavern)
		assert action == Action.MOVE
		assert inputs[0] is market

	def test_move_alias_go(self):
		tavern, market, _, _ = _make_world()
		action, inputs = parse("go market", tavern)
		assert action == Action.MOVE
		assert inputs[0] is market

	def test_shorthand_move_by_room_name(self):
		tavern, market, _, _ = _make_world()
		action, inputs = parse("market", tavern)
		assert action == Action.MOVE
		assert inputs[0] is market

	def test_unresolved_move_returns_string(self):
		room = Room("R")
		action, inputs = parse("move nowhere", room)
		assert action == Action.MOVE
		assert isinstance(inputs[0], str)

	def test_inventory_command(self):
		room = Room("R")
		action, _ = parse("inventory", room)
		assert action == Action.INVENTORY

	def test_inventory_alias(self):
		room = Room("R")
		action, _ = parse("inv", room)
		assert action == Action.INVENTORY

	def test_help_command(self):
		room = Room("R")
		action, _ = parse("help", room)
		assert action == Action.HELP

	def test_quit_command(self):
		room = Room("R")
		action, _ = parse("quit", room)
		assert action == Action.QUIT

	def test_quit_alias(self):
		room = Room("R")
		action, _ = parse("q", room)
		assert action == Action.QUIT

	def test_talk_to_command(self):
		tavern, _, _, npc = _make_world()
		action, inputs = parse("talk to barkeep", tavern)
		assert action == Action.TALK_TO
		assert inputs[0] is npc

	def test_talk_to_unresolved(self):
		room = Room("R")
		action, inputs = parse("talk to ghost", room)
		assert action == Action.TALK_TO
		assert inputs[0] == "ghost"

	def test_look_at_item(self):
		tavern, _, sword, _ = _make_world()
		action, inputs = parse(f"look {sword.name.lower()}", tavern)
		assert action == Action.LOOK
		assert inputs[0] is sword


# -- Execute tests --


class TestExecute:
	def test_look_room_shows_description(self):
		tavern, _, _, _ = _make_world()
		result = execute(Action.LOOK, [tavern], tavern)
		assert any("fire crackles" in m for m in result.messages)

	def test_look_unresolved_shows_error(self):
		room = Room("R")
		result = execute(Action.LOOK, ["phantom"], room)
		assert any("don't see" in m for m in result.messages)

	def test_move_to_room(self):
		tavern, market, _, _ = _make_world()
		result = execute(Action.MOVE, [market], tavern)
		assert result.new_room is market
		assert any("Market" in m for m in result.messages)

	def test_move_unresolved(self):
		room = Room("R")
		result = execute(Action.MOVE, ["nowhere"], room)
		assert result.new_room is None
		assert any("Unknown command" in m for m in result.messages)

	def test_move_empty_input(self):
		room = Room("R")
		result = execute(Action.MOVE, [], room)
		assert any("where" in m.lower() for m in result.messages)

	def test_inventory_empty_room(self):
		room = Room("R")
		result = execute(Action.INVENTORY, [], room)
		assert any("Nothing" in m for m in result.messages)

	def test_inventory_with_items(self):
		tavern, _, sword, _ = _make_world()
		result = execute(Action.INVENTORY, [], tavern)
		assert any(sword.name in m for m in result.messages)

	def test_talk_to_npc(self):
		tavern, _, _, npc = _make_world()
		result = execute(Action.TALK_TO, [npc], tavern)
		assert any("Barkeep" in m for m in result.messages)

	def test_talk_to_nobody(self):
		room = Room("R")
		result = execute(Action.TALK_TO, [], room)
		assert any("whom" in m.lower() for m in result.messages)

	def test_talk_to_unresolved_string(self):
		room = Room("R")
		result = execute(Action.TALK_TO, ["ghost"], room)
		assert any("don't see" in m for m in result.messages)

	def test_help_lists_commands(self):
		tavern, _, _, _ = _make_world()
		result = execute(Action.HELP, [], tavern)
		assert any("Commands" in m for m in result.messages)

	def test_help_lists_exits(self):
		tavern, _, _, _ = _make_world()
		result = execute(Action.HELP, [], tavern)
		assert any("Market" in m for m in result.messages)

	def test_quit_sets_flag(self):
		room = Room("R")
		result = execute(Action.QUIT, [], room)
		assert result.quit is True
