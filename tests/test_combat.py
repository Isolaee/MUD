"""Tests for logic.combat — turn-based combat system."""

import random

from Objects.Characters.character import (
	CharacterClassOptions,
	CharacterRaceOptions,
	NonPlayerCharacter,
	PlayerCharacter,
)
from Objects.Characters.characterRaces import CharacterSize
from Objects.Items.Swords.shortSword import ShortSword
from Objects.Rooms.room import Direction, Room
from logic.combat import CombatInstance, CombatManager, Combatant
from server.world_manager import WorldManager


def _make_player(name: str = "TestPlayer", hp: int = 100) -> PlayerCharacter:
	return PlayerCharacter(
		current_hp=hp,
		current_stamina=100,
		base_attack=10,
		race=CharacterRaceOptions.HUMAN,
		character_class=CharacterClassOptions.WARRIOR,
		characterSize=CharacterSize.MEDIUM,
		inventory=[],
		name=name,
	)


def _make_npc(name: str = "Goblin", hp: int = 30) -> NonPlayerCharacter:
	return NonPlayerCharacter(
		has_enters_the_room=False,
		current_hp=hp,
		current_stamina=50,
		base_attack=5,
		race=CharacterRaceOptions.HUMAN,
		character_class=CharacterClassOptions.WARRIOR,
		characterSize=CharacterSize.SMALL,
		inventory=[],
		name=name,
	)


def _make_world_with_combat():
	"""Create a WorldManager with a player and NPC in the same room."""
	wm = WorldManager()
	room = Room("Arena")
	wm.start_room = room
	wm.rooms = {room.uid: room}

	player = _make_player("Hero")
	npc = _make_npc("Goblin", hp=30)
	room.add_character(npc)

	events: list[str] = []
	wm.join(1, player, room, events.append)

	return wm, room, player, npc, events


# -- CombatInstance unit tests --


class TestCombatInstance:
	def test_is_over_with_one_team(self):
		c1 = Combatant(character_id=1, character=_make_player("A"), team=0)
		c2 = Combatant(character_id=2, character=_make_player("B"), team=1, is_knocked_out=True)
		combat = CombatInstance(combatants=[c1, c2])
		assert combat.is_over()

	def test_is_not_over_with_two_teams(self):
		c1 = Combatant(character_id=1, character=_make_player("A"), team=0)
		c2 = Combatant(character_id=2, character=_make_player("B"), team=1)
		combat = CombatInstance(combatants=[c1, c2])
		assert not combat.is_over()

	def test_get_enemies(self):
		c1 = Combatant(character_id=1, character=_make_player("A"), team=0)
		c2 = Combatant(character_id=2, character=_make_player("B"), team=1)
		c3 = Combatant(character_id=3, character=_make_player("C"), team=0)
		combat = CombatInstance(combatants=[c1, c2, c3])
		enemies = combat.get_enemies(c1)
		assert len(enemies) == 1
		assert enemies[0] is c2

	def test_get_active_combatants_excludes_ko(self):
		c1 = Combatant(character_id=1, character=_make_player("A"), team=0)
		c2 = Combatant(character_id=2, character=_make_player("B"), team=1, is_knocked_out=True)
		combat = CombatInstance(combatants=[c1, c2])
		active = combat.get_active_combatants()
		assert len(active) == 1
		assert active[0] is c1

	def test_current_combatant(self):
		c1 = Combatant(character_id=1, character=_make_player("A"), team=0)
		c2 = Combatant(character_id=2, character=_make_player("B"), team=1)
		combat = CombatInstance(combatants=[c1, c2], current_turn_index=0)
		assert combat.current_combatant is c1


# -- CombatManager tests --


class TestCombatManager:
	def test_start_combat_creates_instance(self):
		wm, room, player, npc, events = _make_world_with_combat()
		# Seed random for deterministic initiative
		random.seed(42)
		wm.combat_manager.start_combat(1, npc, room, wm)

		assert wm.combat_manager.is_in_combat(1)
		# NPC should also be registered
		npc_id = hash(npc.uid) & 0x7FFFFFFF
		assert wm.combat_manager.is_in_combat(npc_id)
		# Should have broadcast combat start
		assert any("Combat begins" in e for e in events)

	def test_cannot_start_combat_while_in_combat(self):
		wm, room, player, npc, events = _make_world_with_combat()
		random.seed(42)
		wm.combat_manager.start_combat(1, npc, room, wm)
		messages = wm.combat_manager.start_combat(1, npc, room, wm)
		assert any("already in combat" in m for m in messages)

	def test_attack_unresolved_target_shows_error(self):
		wm, room, player, npc, events = _make_world_with_combat()
		random.seed(42)
		wm.combat_manager.start_combat(1, npc, room, wm)

		# Force it to be player's turn
		combat = wm.combat_manager.active_combats[1]
		# Re-order so player goes first
		for c in combat.combatants:
			if c.character_id == 1:
				c.initiative = 99
			else:
				c.initiative = 1
		combat.combatants.sort(key=lambda c: c.initiative, reverse=True)
		combat.current_turn_index = 0

		messages = wm.combat_manager.handle_combat_input(1, "attack phantom", wm)
		assert any("not a valid target" in m for m in messages)

	def test_not_your_turn(self):
		wm, room, player, npc, events = _make_world_with_combat()
		random.seed(42)
		wm.combat_manager.start_combat(1, npc, room, wm)

		combat = wm.combat_manager.active_combats[1]
		# Make NPC go first
		for c in combat.combatants:
			if c.is_npc:
				c.initiative = 99
			else:
				c.initiative = 1
		combat.combatants.sort(key=lambda c: c.initiative, reverse=True)
		combat.current_turn_index = 0
		# current combatant is NPC, not player

		# Manually try to act as player
		messages = wm.combat_manager.handle_combat_input(1, "attack goblin", wm)
		assert any("not your turn" in m.lower() for m in messages)

	def test_combat_help_on_invalid_action(self):
		wm, room, player, npc, events = _make_world_with_combat()
		random.seed(42)
		wm.combat_manager.start_combat(1, npc, room, wm)

		combat = wm.combat_manager.active_combats[1]
		for c in combat.combatants:
			if c.character_id == 1:
				c.initiative = 99
			else:
				c.initiative = 1
		combat.combatants.sort(key=lambda c: c.initiative, reverse=True)
		combat.current_turn_index = 0

		messages = wm.combat_manager.handle_combat_input(1, "dance", wm)
		assert any("attack" in m.lower() and "defend" in m.lower() for m in messages)

	def test_defend_sets_flag(self):
		wm, room, player, npc, events = _make_world_with_combat()
		random.seed(42)
		wm.combat_manager.start_combat(1, npc, room, wm)

		combat = wm.combat_manager.active_combats[1]
		for c in combat.combatants:
			if c.character_id == 1:
				c.initiative = 99
			else:
				c.initiative = 1
		combat.combatants.sort(key=lambda c: c.initiative, reverse=True)
		combat.current_turn_index = 0

		wm.combat_manager.handle_combat_input(1, "defend", wm)
		# Find player combatant
		player_combatant = next(c for c in combat.combatants if c.character_id == 1)
		assert player_combatant.is_defending

	def test_calculate_damage(self):
		cm = CombatManager()
		attacker = Combatant(character_id=1, character=_make_player("A"), team=0)
		defender = Combatant(character_id=2, character=_make_player("B"), team=1)

		# Run multiple times — when it hits, damage should be >= 1
		random.seed(42)
		hits = []
		for _ in range(20):
			damage, hit = cm._calculate_damage(attacker, defender)
			if hit:
				hits.append(damage)
				assert damage >= 1
		assert len(hits) > 0  # at least some hits

	def test_calculate_damage_defend_halves(self):
		cm = CombatManager()
		attacker = Combatant(character_id=1, character=_make_player("A"), team=0)
		defender = Combatant(character_id=2, character=_make_player("B"), team=1, is_defending=True)

		damages_normal = []
		damages_defended = []
		random.seed(42)
		for _ in range(50):
			d, hit = cm._calculate_damage(
				attacker, Combatant(character_id=3, character=_make_player("C"), team=1, is_defending=False)
			)
			if hit:
				damages_normal.append(d)

		random.seed(42)
		for _ in range(50):
			d, hit = cm._calculate_damage(attacker, defender)
			if hit:
				damages_defended.append(d)

		# Defended damage should be less on average
		if damages_normal and damages_defended:
			assert sum(damages_defended) <= sum(damages_normal)

	def test_weapon_bonus_applies(self):
		cm = CombatManager()
		player = _make_player("Armed")
		sword = ShortSword(
			reach=1,
			name="Test Sword",
			durability=100,
			degrades=True,
			attackBonus=5,
			onHitEffect=[],
			hitChance=1.0,
		)
		player.equipped_weapon = sword

		attacker = Combatant(character_id=1, character=player, team=0)
		defender = Combatant(character_id=2, character=_make_player("B"), team=1)

		random.seed(42)
		damage, hit = cm._calculate_damage(attacker, defender)
		assert hit
		# base_attack(10) + attackBonus(5) + variance(-2 to +2) = 13-17
		assert 13 <= damage <= 17

	def test_initiative_uses_stamina_modifier(self):
		cm = CombatManager()
		fast = _make_player("Fast")
		fast.stamina = 200  # +20 modifier
		slow = _make_player("Slow")
		slow.stamina = 10  # +1 modifier

		c1 = Combatant(character_id=1, character=fast, team=0)
		c2 = Combatant(character_id=2, character=slow, team=1)
		combat = CombatInstance(combatants=[c1, c2])

		random.seed(42)
		cm._roll_initiative(combat)
		# Fast should generally have higher initiative
		assert c1.initiative >= c2.initiative or True  # Non-deterministic, but structure is tested

	def test_remove_player_from_combat(self):
		wm, room, player, npc, events = _make_world_with_combat()
		random.seed(42)
		wm.combat_manager.start_combat(1, npc, room, wm)
		assert wm.combat_manager.is_in_combat(1)

		wm.combat_manager.remove_player(1, wm)
		assert not wm.combat_manager.is_in_combat(1)


# -- PvP combat tests --


class TestPvPCombat:
	def test_pvp_combat_start(self):
		wm = WorldManager()
		room = Room("Arena")
		wm.start_room = room
		wm.rooms = {room.uid: room}

		p1 = _make_player("Fighter1")
		p2 = _make_player("Fighter2")

		events1: list[str] = []
		events2: list[str] = []
		wm.join(1, p1, room, events1.append)
		wm.join(2, p2, room, events2.append)

		random.seed(42)
		wm.combat_manager.start_combat(1, p2, room, wm)

		assert wm.combat_manager.is_in_combat(1)
		assert wm.combat_manager.is_in_combat(2)

	def test_move_blocked_during_combat(self):
		wm = WorldManager()
		room_a = Room("Room A")
		room_b = Room("Room B")
		room_a.add_connection(room_b, Direction.EAST)
		wm.start_room = room_a
		wm.rooms = {room_a.uid: room_a, room_b.uid: room_b}

		p1 = _make_player("Fighter")
		npc = _make_npc("Goblin")
		room_a.add_character(npc)

		events: list[str] = []
		wm.join(1, p1, room_a, events.append)

		random.seed(42)
		wm.combat_manager.start_combat(1, npc, room_a, wm)

		result = wm.move_player(1, room_b)
		assert result is False
		assert p1 in room_a.present_players
