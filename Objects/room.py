from __future__ import annotations

from typing import TYPE_CHECKING

from Objects.game_object import GameObject

if TYPE_CHECKING:
    from Objects.character import Character
    from Objects.item import Item


class Description:
    def __init__(
        self, short: str, long: str = ""
    ) -> None:
        self.short = short
        self.long = long

    def __repr__(self) -> str:
        return f"Description({self.short!r})"


class Room(GameObject):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.description: Description | None = None
        self.connected_rooms: list[Room] = []
        self.present_items: list[Item] = []
        self.present_characters: list[Character] = []

    def object_type(self) -> str:
        return "Room"

    def add_connection(self, room: Room) -> None:
        self.connected_rooms.append(room)

    def add_item(self, item: Item) -> None:
        self.present_items.append(item)

    def add_character(
        self, character: Character
    ) -> None:
        self.present_characters.append(character)
