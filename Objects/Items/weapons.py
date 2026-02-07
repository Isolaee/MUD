from __future__ import annotations

from abc import ABC
from enum import Enum, auto

from Objects.item import Item, ItemType


class DamageType(Enum):
	PHYSICAL = auto()
	FIRE = auto()
	ICE = auto()
	LIGHTNING = auto()
	POISON = auto()
	NECROTIC = auto()
	RADIANT = auto()
	PSYCHIC = auto()


class Weapon(Item, ABC):
	"""Virtual base class for all weapons."""

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
