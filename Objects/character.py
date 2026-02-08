"""Character hierarchy for player and non-player characters.

Defines the abstract Character base and two concrete subclasses:
- PlayerCharacter: controlled by a human player.
- NonPlayerCharacter: controlled by game logic / AI.

Currently minimal — stats, abilities, and behaviour will be
added as the game evolves.
"""

from __future__ import annotations

from abc import ABC

from Objects.game_object import GameObject


class Character(GameObject, ABC):
	"""Virtual base class for all characters.

	Inherits identity, properties, and tags from GameObject.
	Future additions: health, stats, equipment slots, etc.
	"""

	def __init__(self, name: str) -> None:
		super().__init__(name)

	def object_type(self) -> str:
		return "Character"


class PlayerCharacter(Character):
	"""A player-controlled character.

	Represents the human player's avatar in the game world.
	"""

	def __init__(self, name: str) -> None:
		super().__init__(name)

	def object_type(self) -> str:
		return "PlayerCharacter"


class NonPlayerCharacter(Character):
	"""An NPC (non-player character).

	Represents characters controlled by game logic, such as
	merchants, quest-givers, or enemies.
	"""

	def __init__(self, name: str) -> None:
		super().__init__(name)

	def object_type(self) -> str:
		return "NonPlayerCharacter"
