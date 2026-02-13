"""Character class definitions for the MUD.

Each character class defines base stat modifiers and abilities
that differentiate play styles (Warrior, Mage, Rogue, Cleric).
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass


@dataclass
class StatModifiers:
	"""Stat adjustments applied on top of base character stats."""

	hp: int
	stamina: int
	attack: int


class CharacterClass(ABC):
	"""Abstract base for all character classes.

	All concrete subclasses are automatically discoverable via
	``get_all_classes()`` — no need to register them manually.
	Subclasses must call super().__init__() with description
	and stat_modifiers to define their class traits.
	"""

	def __init__(self, description: str, stat_modifiers: StatModifiers) -> None:
		self.description = description
		self.stat_modifiers = stat_modifiers

	@property
	def className(self) -> str:
		"""Returns the class name derived from the class type."""
		return self.__class__.__name__


def get_all_classes() -> dict[str, type[CharacterClass]]:
	"""Return a mapping of uppercase name -> class for every concrete CharacterClass."""
	return {cls.__name__.upper(): cls for cls in CharacterClass.__subclasses__()}


class Warrior(CharacterClass):
	"""Heavy melee fighter with high HP and attack."""

	def __init__(self) -> None:
		super().__init__(
			description="A battle-hardened fighter who relies on strength and endurance.",
			stat_modifiers=StatModifiers(hp=20, stamina=10, attack=5),
		)


class Mage(CharacterClass):
	"""Arcane spellcaster with low HP but powerful abilities."""

	def __init__(self) -> None:
		super().__init__(
			description="A wielder of arcane magic, fragile but devastatingly powerful.",
			stat_modifiers=StatModifiers(hp=-10, stamina=5, attack=-2),
		)


class Rogue(CharacterClass):
	"""Agile fighter favouring speed and precision over brute force."""

	def __init__(self) -> None:
		super().__init__(
			description="A cunning and agile fighter who strikes from the shadows.",
			stat_modifiers=StatModifiers(hp=-5, stamina=20, attack=3),
		)


class Cleric(CharacterClass):
	"""Divine healer and support with balanced stats."""

	def __init__(self) -> None:
		super().__init__(
			description="A divine servant who heals allies and smites the unholy.",
			stat_modifiers=StatModifiers(hp=10, stamina=5, attack=0),
		)
