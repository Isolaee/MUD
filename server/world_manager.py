"""Shared world state for true multiplayer.

The WorldManager is created once at server startup and passed to every
SSHGameSession.  It owns the canonical room graph, tracks which players
are in which rooms, and broadcasts events to the right sessions.

Concurrency safety: the asyncio event loop is single-threaded, so
synchronous code blocks are atomic — no locks needed as long as we
don't ``await`` between a check and a mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from Objects.Rooms.room import Room

if TYPE_CHECKING:
	from Objects.Characters.character import PlayerCharacter
	from Objects.Items.item import Item


@dataclass
class GameSession:
	"""Tracks a single active player in the world."""

	character_id: int
	player: PlayerCharacter
	room: Room
	event_callback: Callable[[str], None]


class WorldManager:
	"""Singleton shared world state, created once at server startup."""

	def __init__(self) -> None:
		self.rooms: dict[str, Room] = {}
		self.start_room: Room | None = None
		self.sessions: dict[int, GameSession] = {}  # character_id -> session

	# -- world loading --------------------------------------------------------

	def load_world(self) -> None:
		"""Load the game world from area definitions.

		Called once at server startup.  Imports the demo area modules and
		collects all rooms into ``self.rooms`` keyed by uid.
		"""
		# Import area modules — they create rooms and wire connections
		# on import.  We just need to grab the objects they expose.
		from World.demoArea import START_ROOM

		self.start_room = START_ROOM
		self._collect_rooms(START_ROOM)

	def _collect_rooms(self, start: Room) -> None:
		"""BFS through the room graph starting from *start*."""
		visited: set[str] = set()
		queue = [start]
		while queue:
			room = queue.pop(0)
			if room.uid in visited:
				continue
			visited.add(room.uid)
			self.rooms[room.uid] = room
			for connected in room.connected_rooms.values():
				if connected.uid not in visited:
					queue.append(connected)

	# -- player presence ------------------------------------------------------

	def join(
		self,
		character_id: int,
		player: PlayerCharacter,
		room: Room,
		event_callback: Callable[[str], None],
	) -> None:
		"""Register a player entering the world."""
		session = GameSession(
			character_id=character_id,
			player=player,
			room=room,
			event_callback=event_callback,
		)
		self.sessions[character_id] = session
		room.present_players.append(player)
		self.broadcast_to_room(
			room,
			f"[dim]{player.name} has entered the world.[/dim]",
			exclude=character_id,
		)

	def leave(self, character_id: int) -> None:
		"""Remove a player from the world (disconnect / logout)."""
		session = self.sessions.pop(character_id, None)
		if session is None:
			return
		room = session.room
		player = session.player
		if player in room.present_players:
			room.present_players.remove(player)
		self.broadcast_to_room(
			room,
			f"[dim]{player.name} has left the world.[/dim]",
			exclude=character_id,
		)
		# Persist character state
		from server.database import save_character

		save_character(character_id, player.hp, player.stamina)

	def move_player(self, character_id: int, target_room: Room) -> None:
		"""Atomically move a player between rooms and broadcast to both."""
		session = self.sessions.get(character_id)
		if session is None:
			return
		old_room = session.room
		player = session.player

		# Remove from old room
		if player in old_room.present_players:
			old_room.present_players.remove(player)
		self.broadcast_to_room(
			old_room,
			f"[dim]{player.name} has left.[/dim]",
			exclude=character_id,
		)

		# Add to new room
		target_room.present_players.append(player)
		session.room = target_room
		self.broadcast_to_room(
			target_room,
			f"[dim]{player.name} has arrived.[/dim]",
			exclude=character_id,
		)

	# -- event broadcasting ---------------------------------------------------

	def broadcast_to_room(self, room: Room, message: str, exclude: int | None = None) -> None:
		"""Send a message to all players in a room, optionally excluding one."""
		for session in self.sessions.values():
			if session.room is room and session.character_id != exclude:
				session.event_callback(message)

	# -- atomic actions -------------------------------------------------------

	def pickup_item(self, character_id: int, item: Item, room: Room) -> bool:
		"""Try to pick up an item. Returns False if already taken."""
		if item not in room.present_items:
			return False
		room.present_items.remove(item)
		session = self.sessions[character_id]
		session.player.inventory.append(item)
		self.broadcast_to_room(
			room,
			f"[dim]{session.player.name} picks up {item.name}.[/dim]",
			exclude=character_id,
		)
		return True

	def drop_item(self, character_id: int, item: Item, room: Room) -> bool:
		"""Drop an item from inventory into the room."""
		session = self.sessions.get(character_id)
		if session is None or item not in session.player.inventory:
			return False
		session.player.inventory.remove(item)
		room.present_items.append(item)
		self.broadcast_to_room(
			room,
			f"[dim]{session.player.name} drops {item.name}.[/dim]",
			exclude=character_id,
		)
		return True

	def get_players_in_room(self, room: Room) -> list[PlayerCharacter]:
		"""Return all player characters currently in a room."""
		return list(room.present_players)
