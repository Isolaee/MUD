"""Weapon base class and damage-type definitions.

Weapons are Items that can be used in combat.  Each weapon carries
an attack bonus, hit chance, damage type, and a list of effects
triggered on a successful hit.
"""

from __future__ import annotations

from abc import ABC
from enum import Enum, auto

from Objects.item import Item, ItemType


class DamageType(Enum):
	"""Elemental / physical damage types used by the combat system."""

	PHYSICAL = auto()
	FIRE = auto()
	ICE = auto()
	LIGHTNING = auto()
	POISON = auto()
	NECROTIC = auto()
	RADIANT = auto()
	PSYCHIC = auto()


class Weapon(Item, ABC):
	"""Virtual base class for all weapons.

	Automatically sets its ItemType to WEAPONS.

	Attributes:
		attackBonus: Flat modifier added to attack rolls.
		onHitEffect: List of effects applied when the weapon hits.
		hitChance: Probability (0.0-1.0) of landing a hit.
		damageType: The type of damage this weapon deals.
	"""

	def __init__(
		self,
		name: str,
		durability: int,
		degrades: bool,
		attackBonus: int,
		onHitEffect: list,
		is_magical: bool = False,
		hitChance: float = 1.0,
		damageType: DamageType = DamageType.PHYSICAL,
	) -> None:
		super().__init__(name, ItemType.WEAPONS, durability, degrades, is_magical)
		self.attackBonus: int = attackBonus
		self.onHitEffect: list = onHitEffect
		self.hitChance: float = hitChance
		self.damageType: DamageType = damageType

	def object_type(self) -> str:
		return "Virtual Weapon"
