"""Tests for server.world_manager shared world state."""

from Objects.Characters.character import (
	CharacterClassOptions,
	CharacterRaceOptions,
	PlayerCharacter,
)
from Objects.Characters.characterRaces import CharacterSize
from Objects.Rooms.room import Direction, Room
from server.world_manager import WorldManager


def _make_player(name: str = "TestPlayer") -> PlayerCharacter:
	return PlayerCharacter(
		current_hp=100,
		current_stamina=100,
		base_attack=10,
		race=CharacterRaceOptions.HUMAN,
		character_class=CharacterClassOptions.WARRIOR,
		characterSize=CharacterSize.MEDIUM,
		inventory=[],
		name=name,
	)


def _make_world() -> WorldManager:
	"""Create a small test world with two connected rooms."""
	wm = WorldManager()
	room_a = Room("Room A")
	room_b = Room("Room B")
	room_a.add_connection(room_b, Direction.EAST)
	wm.start_room = room_a
	wm.rooms = {room_a.uid: room_a, room_b.uid: room_b}
	return wm


def test_join_adds_player_to_room():
	wm = _make_world()
	player = _make_player()
	events: list[str] = []
	wm.join(1, player, wm.start_room, events.append)

	assert player in wm.start_room.present_players
	assert 1 in wm.sessions


def test_leave_removes_player():
	wm = _make_world()
	player = _make_player()
	wm.join(1, player, wm.start_room, lambda m: None)
	# Monkeypatch save_character to avoid DB dependency
	import server.database

	original = server.database.save_character
	server.database.save_character = lambda *a, **k: None
	try:
		wm.leave(1)
	finally:
		server.database.save_character = original

	assert player not in wm.start_room.present_players
	assert 1 not in wm.sessions


def test_move_player_broadcasts():
	wm = _make_world()
	player = _make_player("Mover")
	room_a = wm.start_room
	room_b = list(room_a.connected_rooms.values())[0]

	events_a: list[str] = []
	events_b: list[str] = []

	# Place an observer in room B
	observer = _make_player("Observer")
	wm.join(2, observer, room_b, events_b.append)

	# Player joins room A then moves to B
	wm.join(1, player, room_a, events_a.append)
	wm.move_player(1, room_b)

	assert player not in room_a.present_players
	assert player in room_b.present_players
	assert wm.sessions[1].room is room_b
	# Observer in room B should see arrival
	assert any("Mover" in e and "arrived" in e for e in events_b)


def test_broadcast_excludes_sender():
	wm = _make_world()
	events_self: list[str] = []
	events_other: list[str] = []

	p1 = _make_player("P1")
	p2 = _make_player("P2")
	wm.join(1, p1, wm.start_room, events_self.append)
	wm.join(2, p2, wm.start_room, events_other.append)

	wm.broadcast_to_room(wm.start_room, "Hello!", exclude=1)
	assert "Hello!" in events_other
	assert "Hello!" not in events_self


def test_get_players_in_room():
	wm = _make_world()
	p1 = _make_player("A")
	p2 = _make_player("B")
	wm.join(1, p1, wm.start_room, lambda m: None)
	wm.join(2, p2, wm.start_room, lambda m: None)

	players = wm.get_players_in_room(wm.start_room)
	assert len(players) == 2
