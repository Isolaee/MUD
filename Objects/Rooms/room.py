"""Room (location) management, directions, and descriptions.

Rooms are the fundamental nodes of the game world graph.  Each room
holds a description, a set of directional connections to neighbouring
rooms, and lists of items and characters currently present.

Connections are always bidirectional — calling ``add_connection`` on
room A towards room B automatically creates the reverse link.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from Objects.game_object import GameObject

if TYPE_CHECKING:
	from Objects.Characters.character import Character, PlayerCharacter
	from Objects.Items.item import Item


class Direction(Enum):
	"""Eight compass directions used for room-to-room navigation."""

	NORTH = auto()
	NORTH_EAST = auto()
	EAST = auto()
	SOUTH_EAST = auto()
	SOUTH = auto()
	SOUTH_WEST = auto()
	WEST = auto()
	NORTH_WEST = auto()


# Mapping from each direction to its 180-degree opposite.
OPPOSITE: dict[Direction, Direction] = {
	Direction.NORTH: Direction.SOUTH,
	Direction.NORTH_EAST: Direction.SOUTH_WEST,
	Direction.EAST: Direction.WEST,
	Direction.SOUTH_EAST: Direction.NORTH_WEST,
	Direction.SOUTH: Direction.NORTH,
	Direction.SOUTH_WEST: Direction.NORTH_EAST,
	Direction.WEST: Direction.EAST,
	Direction.NORTH_WEST: Direction.SOUTH_EAST,
}

# Unit (dx, dy) vectors for each direction.
# +x = east, +y = south (screen convention used by the map renderer).
DIR_VECTOR: dict[Direction, tuple[int, int]] = {
	Direction.NORTH: (0, -1),
	Direction.NORTH_EAST: (1, -1),
	Direction.EAST: (1, 0),
	Direction.SOUTH_EAST: (1, 1),
	Direction.SOUTH: (0, 1),
	Direction.SOUTH_WEST: (-1, 1),
	Direction.WEST: (-1, 0),
	Direction.NORTH_WEST: (-1, -1),
}


class Description:
	"""Short and long textual descriptions attached to a room.

	Attributes:
	    short: One-line summary shown on the map or in brief mode.
	    long: Full paragraph displayed when the player LOOKs.
	"""

	def __init__(
		self,
		short: str,
		long: str = "",
	) -> None:
		self.short = short
		self.long = long

	def __repr__(self) -> str:
		return f"Description({self.short!r})"


class Room(GameObject):
	"""A single location in the game world.

	Rooms form a directed graph connected via compass directions.
	Each room can hold items and characters.

	Attributes:
	    description: Optional short/long text for the room.
	    connected_rooms: Directional map of neighbouring rooms.
	    present_items: Items currently lying on the floor.
	    present_characters: Characters currently in the room.
	"""

	def __init__(self, name: str) -> None:
		super().__init__(name)
		self.description: Description | None = None
		self.connected_rooms: dict[Direction, Room] = {}
		self.present_items: list[Item] = []
		self.present_characters: list[Character] = []
		self.present_players: list[PlayerCharacter] = []

	def object_type(self) -> str:
		return "Room"

	def add_connection(self, room: Room, direction: Direction) -> None:
		"""Create a bidirectional link between this room and *room*.

		Both the forward (self -> room) and reverse (room -> self)
		connections are created at once.

		Raises:
		    ValueError: If either direction slot is already occupied,
		        preventing accidental overwrites.
		"""
		opposite = OPPOSITE[direction]

		if direction in self.connected_rooms:
			raise ValueError(
				f"{self.name}: {direction.name} is already occupied by {self.connected_rooms[direction].name}"
			)
		if opposite in room.connected_rooms:
			raise ValueError(
				f"{room.name}: {opposite.name} is already occupied by {room.connected_rooms[opposite].name}"
			)

		self.connected_rooms[direction] = room
		room.connected_rooms[opposite] = self

	def add_item(self, item: Item) -> None:
		"""Place an item in this room."""
		self.present_items.append(item)

	def add_character(self, character: Character) -> None:
		"""Add a character to this room's occupant list."""
		self.present_characters.append(character)
