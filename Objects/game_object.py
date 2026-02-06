from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import uuid4


class GameObject(ABC):
    """Virtual base class for all game objects.

    Every entity in the game (rooms, characters, items)
    inherits from this.
    """

    def __init__(self, name: str) -> None:
        self.uid: str = uuid4().hex
        self.name: str = name
        self.tags: set[str] = set()
        self._properties: dict[str, object] = {}

    # -- data helpers --

    def get_prop(
        self, key: str, default: object = None
    ) -> object:
        return self._properties.get(key, default)

    def set_prop(self, key: str, value: object) -> None:
        self._properties[key] = value

    def has_prop(self, key: str) -> bool:
        return key in self._properties

    def remove_prop(self, key: str) -> None:
        self._properties.pop(key, None)

    # -- tag helpers --

    def add_tag(self, tag: str) -> None:
        self.tags.add(tag)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def remove_tag(self, tag: str) -> None:
        self.tags.discard(tag)

    # -- identity --

    @abstractmethod
    def object_type(self) -> str:
        """Return the type label, e.g. 'room', 'item'."""

    def __repr__(self) -> str:
        return (
            f"{self.object_type()}("
            f"{self.name!r}, uid={self.uid[:8]})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GameObject):
            return NotImplemented
        return self.uid == other.uid

    def __hash__(self) -> int:
        return hash(self.uid)
