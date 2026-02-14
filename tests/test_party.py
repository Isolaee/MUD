"""Tests for logic.party — party system."""

from Objects.Characters.character import (
	CharacterClassOptions,
	CharacterRaceOptions,
	PlayerCharacter,
)
from Objects.Characters.characterRaces import CharacterSize
from Objects.Rooms.room import Direction, Room
from logic.party import MAX_PARTY_SIZE
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


def _make_world_with_players(count: int = 2):
	"""Create a WorldManager with *count* players in the same room."""
	wm = WorldManager()
	room = Room("Tavern")
	wm.start_room = room
	wm.rooms = {room.uid: room}

	players = []
	events = []
	for i in range(count):
		p = _make_player(f"Player{i + 1}")
		ev: list[str] = []
		wm.join(i + 1, p, room, ev.append)
		players.append(p)
		events.append(ev)

	return wm, room, players, events


class TestPartyInvite:
	def test_invite_sends_message_to_invitee(self):
		wm, room, players, events = _make_world_with_players(2)
		pm = wm.party_manager

		messages = pm.invite(1, 2, wm)
		assert any("Invite sent" in m for m in messages)
		# Invitee should receive notification
		assert any("invites you" in e for e in events[1])

	def test_invite_not_in_same_room(self):
		wm = WorldManager()
		room_a = Room("Room A")
		room_b = Room("Room B")
		wm.start_room = room_a
		wm.rooms = {room_a.uid: room_a, room_b.uid: room_b}

		p1 = _make_player("P1")
		p2 = _make_player("P2")
		wm.join(1, p1, room_a, lambda m: None)
		wm.join(2, p2, room_b, lambda m: None)

		messages = wm.party_manager.invite(1, 2, wm)
		assert any("not in this room" in m for m in messages)

	def test_invite_duplicate_rejected(self):
		wm, room, players, events = _make_world_with_players(2)
		pm = wm.party_manager

		pm.invite(1, 2, wm)
		messages = pm.invite(1, 2, wm)
		assert any("pending invite" in m for m in messages)


class TestPartyAcceptDecline:
	def test_accept_forms_party(self):
		wm, room, players, events = _make_world_with_players(2)
		pm = wm.party_manager

		pm.invite(1, 2, wm)
		messages = pm.accept(2, wm)
		assert any("joined" in m for m in messages)
		assert pm.get_party_members(1) == [1, 2]
		assert pm.get_party_members(2) == [1, 2]

	def test_accept_no_invite(self):
		wm, room, players, events = _make_world_with_players(2)
		pm = wm.party_manager

		messages = pm.accept(2, wm)
		assert any("no pending" in m.lower() for m in messages)

	def test_decline_removes_invite(self):
		wm, room, players, events = _make_world_with_players(2)
		pm = wm.party_manager

		pm.invite(1, 2, wm)
		messages = pm.decline(2, wm)
		assert any("declined" in m.lower() for m in messages)
		# Invite should be gone
		assert 2 not in pm.invites

	def test_decline_no_invite(self):
		wm, room, players, events = _make_world_with_players(2)
		pm = wm.party_manager

		messages = pm.decline(2, wm)
		assert any("no pending" in m.lower() for m in messages)


class TestPartyMembership:
	def test_party_max_size(self):
		count = MAX_PARTY_SIZE + 1
		wm, room, players, events = _make_world_with_players(count)
		pm = wm.party_manager

		# Form a full party
		for i in range(1, MAX_PARTY_SIZE):
			pm.invite(1, i + 1, wm)
			pm.accept(i + 1, wm)

		assert len(pm.get_party_members(1)) == MAX_PARTY_SIZE

		# Try to invite one more — should be blocked by size check
		pm.invite(1, MAX_PARTY_SIZE + 1, wm)
		pm.accept(MAX_PARTY_SIZE + 1, wm)
		assert len(pm.get_party_members(1)) <= MAX_PARTY_SIZE

	def test_leave_party(self):
		wm, room, players, events = _make_world_with_players(3)
		pm = wm.party_manager

		pm.invite(1, 2, wm)
		pm.accept(2, wm)
		pm.invite(1, 3, wm)
		pm.accept(3, wm)

		messages = pm.leave_party(2, wm)
		assert any("left" in m.lower() for m in messages)
		assert 2 not in pm.get_party_members(1)
		assert len(pm.get_party_members(1)) == 2

	def test_leader_leave_promotes(self):
		wm, room, players, events = _make_world_with_players(3)
		pm = wm.party_manager

		pm.invite(1, 2, wm)
		pm.accept(2, wm)
		pm.invite(1, 3, wm)
		pm.accept(3, wm)

		pm.leave_party(1, wm)
		# Party should still exist with new leader
		members = pm.get_party_members(2)
		assert 2 in members
		assert 3 in members
		assert 1 not in members

	def test_leave_disbands_duo(self):
		wm, room, players, events = _make_world_with_players(2)
		pm = wm.party_manager

		pm.invite(1, 2, wm)
		pm.accept(2, wm)
		pm.leave_party(2, wm)

		# Should be disbanded
		assert pm._find_party_leader(1) is None

	def test_show_party(self):
		wm, room, players, events = _make_world_with_players(2)
		pm = wm.party_manager

		pm.invite(1, 2, wm)
		pm.accept(2, wm)

		messages = pm.show_party(1, wm)
		assert any("Party members" in m for m in messages)
		assert any("Player1" in m for m in messages)
		assert any("Player2" in m for m in messages)

	def test_show_party_when_not_in_party(self):
		wm, room, players, events = _make_world_with_players(1)
		pm = wm.party_manager

		messages = pm.show_party(1, wm)
		assert any("not in a party" in m.lower() for m in messages)

	def test_get_party_members_in_room(self):
		wm = WorldManager()
		room_a = Room("Room A")
		room_b = Room("Room B")
		room_a.add_connection(room_b, Direction.EAST)
		wm.start_room = room_a
		wm.rooms = {room_a.uid: room_a, room_b.uid: room_b}

		p1 = _make_player("P1")
		p2 = _make_player("P2")
		p3 = _make_player("P3")
		wm.join(1, p1, room_a, lambda m: None)
		wm.join(2, p2, room_a, lambda m: None)
		wm.join(3, p3, room_b, lambda m: None)

		pm = wm.party_manager
		pm.invite(1, 2, wm)
		pm.accept(2, wm)
		pm.invite(1, 3, wm)
		pm.accept(3, wm)

		# Only P1 and P2 are in room_a
		in_room = pm.get_party_members_in_room(1, room_a.uid, wm)
		assert 1 in in_room
		assert 2 in in_room
		assert 3 not in in_room

	def test_remove_player_cleanup(self):
		wm, room, players, events = _make_world_with_players(2)
		pm = wm.party_manager

		pm.invite(1, 2, wm)
		pm.accept(2, wm)

		pm.remove_player(2, wm)
		assert 2 not in pm.get_party_members(1)
