from __future__ import annotations

from abc import ABC

from Objects.game_object import GameObject


class Item(GameObject, ABC):
    """Virtual base class for all game items."""

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def object_type(self) -> str:
        return "Item"
