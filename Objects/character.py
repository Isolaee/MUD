from __future__ import annotations

from abc import ABC

from Objects.game_object import GameObject


class Character(GameObject, ABC):
    """Virtual base class for all characters."""

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def object_type(self) -> str:
        return "Character"


class PlayerCharacter(Character):
    """A player-controlled character."""

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def object_type(self) -> str:
        return "PlayerCharacter"


class NonPlayerCharacter(Character):
    """An NPC (non-player character)."""

    def __init__(self, name: str) -> None:
        super().__init__(name)

    def object_type(self) -> str:
        return "NonPlayerCharacter"
