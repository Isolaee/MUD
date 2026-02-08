"""Character hierarchy for player and non-player characters.

Defines the abstract Character base and two concrete subclasses:
- PlayerCharacter: controlled by a human player.
- NonPlayerCharacter: controlled by game logic / AI.

Currently minimal — stats, abilities, and behaviour will be
added as the game evolves.
"""

from __future__ import annotations

from abc import ABC
from enum import Enum, auto

from Objects.game_object import GameObject


class CharacterType(Enum):
	PLAYER = auto()
	NPC = auto()


class Race(Enum):
	HUMAN = auto()
	ELF = auto()
	ORC = auto()
	GNOME = auto()


class CharacterSize(Enum):
	MINIATURE = auto()  # Doll size, tiny creatures
	SMALL = auto()  # Gnomes, halflings and goblins
	MEDIUM = auto()  # Humans, elves, orcs and most common creatures
	LARGE = auto()  # Ogres, trolls. Size is about a elephant
	HUGE = auto()  # Giants, dragons and other huge creatures. Real life size is about a house
	HUMONGOUS = auto()  # Titans,  other humongous creatures. Real life size is about a castle or a mountain


class Character(GameObject, ABC):
	"""Virtual base class for all characters.

	Inherits identity, properties, and tags from GameObject.
	Future additions: health, stats, equipment slots, etc.
	"""

	def __init__(self, name: str) -> None:
		super().__init__(name)


class PlayerCharacter(Character):
	"""A player-controlled character.

	Represents the human player's avatar in the game world.
	"""

	def __init__(
		self,
		current_hp: int,
		current_stamina: int,
		base_attack: int,
		race: Race,
		characterSize: CharacterSize,
		inventory: list,
		**kwargs,
	) -> None:
		super().__init__(**kwargs)
		self.hp = current_hp
		self.stamina = current_stamina
		self.base_attack = base_attack  # Do we want to derive base attack value from race? Base attack would not be defined on creation but calculated on demand based on race, size and items.
		self.race = race
		self.size = characterSize
		self.inventory = inventory

	def object_type(self) -> CharacterType:
		return CharacterType.PLAYER


class NonPlayerCharacter(PlayerCharacter):
	"""An NPC (non-player character).

	Represents characters controlled by game logic, such as
	merchants, quest-givers, or enemies.
	"""

	def __init__(self, has_enters_the_room: bool, **kwargs) -> None:
		super().__init__(**kwargs)
		self.has_enters_the_room = has_enters_the_room

	def object_type(self) -> CharacterType:
		return CharacterType.NPC
