"""
Race definitions for player characters.
Each race provides unique stat modifiers and traits that influence gameplay.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from enum import Enum, auto


class CharacterSize(Enum):
	MINIATURE = auto()  # Doll size, tiny creatures
	SMALL = auto()  # Gnomes, halflings and goblins
	MEDIUM = auto()  # Humans, elves, orcs and most common creatures
	LARGE = auto()  # Ogres, trolls. Size is about a elephant
	HUGE = auto()  # Giants, dragons and other huge creatures. Real life size is about a house
	HUMONGOUS = auto()  # Titans, other humongous creatures. Real life size is about a castle or a mountain


@dataclass
class StatModifiers:
	"""Stat adjustments applied on top of base character stats."""

	hp: int
	stamina: int
	attack: int


class CharacterRace(ABC):
	"""Abstract base for all character races.

	Subclasses must call super().__init__() with description, size,
	and stat_modifiers to define their racial traits.
	"""

	def __init__(self, description: str, size: CharacterSize, stat_modifiers: StatModifiers) -> None:
		self.description = description
		self.size = size
		self.stat_modifiers = stat_modifiers

	@property
	def race_name(self) -> str:
		"""Returns the race name derived from the class name."""
		return self.__class__.__name__


def get_all_races() -> dict[str, type[CharacterRace]]:
	"""Return a mapping of uppercase name -> class for every concrete CharacterRace."""
	return {cls.__name__.upper(): cls for cls in CharacterRace.__subclasses__()}


class Human(CharacterRace):
	"""Versatile and balanced, humans have no extreme strengths or weaknesses."""

	def __init__(self) -> None:
		super().__init__(
			description="A versatile and adaptable race with no extreme strengths or weaknesses.",
			size=CharacterSize.MEDIUM,
			stat_modifiers=StatModifiers(hp=0, stamina=0, attack=0),
		)
