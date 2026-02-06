from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from Objects.game_object import GameObject

if TYPE_CHECKING:
    from Objects.character import Character
    from Objects.item import Item


class Direction(Enum):
    NORTH = auto()
    NORTH_EAST = auto()
    EAST = auto()
    SOUTH_EAST = auto()
    SOUTH = auto()
    SOUTH_WEST = auto()
    WEST = auto()
    NORTH_WEST = auto()


OPPOSITE = {
    Direction.NORTH: Direction.SOUTH,
    Direction.NORTH_EAST: Direction.SOUTH_WEST,
    Direction.EAST: Direction.WEST,
    Direction.SOUTH_EAST: Direction.NORTH_WEST,
    Direction.SOUTH: Direction.NORTH,
    Direction.SOUTH_WEST: Direction.NORTH_EAST,
    Direction.WEST: Direction.EAST,
    Direction.NORTH_WEST: Direction.SOUTH_EAST,
}

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
    def __init__(
        self, short: str, long: str = "",
    ) -> None:
        self.short = short
        self.long = long

    def __repr__(self) -> str:
        return f"Description({self.short!r})"


class Room(GameObject):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.description: Description | None = None
        self.connected_rooms: dict[Direction, Room] = {}
        self.present_items: list[Item] = []
        self.present_characters: list[Character] = []

    def object_type(self) -> str:
        return "Room"

    def add_connection(
        self, room: Room, direction: Direction
    ) -> None:
        opposite = OPPOSITE[direction]

        if direction in self.connected_rooms:
            raise ValueError(
                f"{self.name}: {direction.name} "
                "is already occupied by "
                f"{self.connected_rooms[direction].name}"
            )
        if opposite in room.connected_rooms:
            raise ValueError(
                f"{room.name}: {opposite.name} "
                "is already occupied by "
                f"{room.connected_rooms[opposite].name}"
            )

        self.connected_rooms[direction] = room
        room.connected_rooms[opposite] = self

    def add_item(self, item: Item) -> None:
        self.present_items.append(item)

    def add_character(
        self, character: Character
    ) -> None:
        self.present_characters.append(character)
