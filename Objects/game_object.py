"""Base class for every entity in the game world.

GameObject is an abstract base class that provides:
- A unique identifier (UUID) for each instance.
- A generic key/value property store for extensible attributes.
- A lightweight tag system for runtime categorisation and querying.
- Identity semantics (equality/hashing) based on UID.

All concrete game entities (Room, Character, Item, etc.) ultimately
inherit from this class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import uuid4


class GameObject(ABC):
	"""Virtual base class for all game objects.

	Every entity in the game (rooms, characters, items)
	inherits from this.

	Attributes:
	    uid: Unique hex identifier generated at creation time.
	    name: Human-readable display name.
	    tags: Arbitrary string tags used for categorisation.
	    _properties: Internal dict for storing ad-hoc key/value data.
	"""

	def __init__(self, name: str) -> None:
		self.uid: str = uuid4().hex
		self.name: str = name
		self.tags: set[str] = set()
		self._properties: dict[str, object] = {}

	# -- data helpers --

	def get_prop(self, key: str, default: object = None) -> object:
		"""Retrieve a property value, returning *default* if absent."""
		return self._properties.get(key, default)

	def set_prop(self, key: str, value: object) -> None:
		"""Store an arbitrary key/value property on this object."""
		self._properties[key] = value

	def has_prop(self, key: str) -> bool:
		"""Return True if the property *key* exists."""
		return key in self._properties

	def remove_prop(self, key: str) -> None:
		"""Remove a property by key (no-op if absent)."""
		self._properties.pop(key, None)

	# -- tag helpers --

	def add_tag(self, tag: str) -> None:
		"""Add a tag to this object."""
		self.tags.add(tag)

	def has_tag(self, tag: str) -> bool:
		"""Return True if this object carries the given tag."""
		return tag in self.tags

	def remove_tag(self, tag: str) -> None:
		"""Remove a tag (no-op if absent)."""
		self.tags.discard(tag)

	# -- identity --

	@abstractmethod
	def object_type(self) -> str:
		"""Return a human-readable type label, e.g. ``'Room'``, ``'Item'``.

		Subclasses must override this to provide a type string
		used in ``__repr__`` and debugging output.
		"""

	def __repr__(self) -> str:
		return f"{self.object_type()}({self.name!r}, uid={self.uid[:8]})"

	def __eq__(self, other: object) -> bool:
		"""Two GameObjects are equal iff they share the same UID."""
		if not isinstance(other, GameObject):
			return NotImplemented
		return self.uid == other.uid

	def __hash__(self) -> int:
		"""Hash based on UID so GameObjects work in sets and dicts."""
		return hash(self.uid)
