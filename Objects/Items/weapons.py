from __future__ import annotations

from abc import ABC

from Objects.item import Item, ItemType


class Weapon(Item, ABC):
    """Virtual base class for all weapons."""

    def __init__(
        self,
        name: str,
        durability: int,
        degrades: bool,
        is_magical: bool = False,
    ) -> None:
        super().__init__(
            name, ItemType.WEAPONS, is_magical
        )
        self.durability: int = durability
        self.degrades: bool = degrades

    def object_type(self) -> str:
        return "Virtual Weapon"


class Sword(Weapon):
    def __init__(
        self,
        name: str,
        durability: int,
        degrades: bool,
        is_magical: bool = False,
    ) -> None:
        super().__init__(name, durability, degrades, is_magical)

    def object_type(self) -> str:
        return "Sword"

    def get_name(self) -> str:
        return self.name
