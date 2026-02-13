"""Item base class and item-type catalogue.

Items are GameObjects that can exist inside rooms or (eventually)
inside a character's inventory.  Each item has a type category
(weapon, armour, tool, etc.), durability tracking, and a magical flag.
"""

from __future__ import annotations

from abc import ABC
from enum import Enum, auto

from Objects.game_object import GameObject


class ItemType(Enum):
	"""Broad categories that every item belongs to.

	Used for filtering, shop sorting, and equipment-slot validation.
	"""

	GEAR = auto()
	ARMOR_AND_SHIELDS = auto()
	TRINKETS = auto()
	WEAPONS = auto()
	FIREARMS = auto()
	EXPLOSIVES = auto()
	WONDROUS_ITEMS = auto()
	CURRENCY = auto()
	POISONS = auto()
	TOOLS = auto()
	SIEGE_EQUIPMENT = auto()


class Item(GameObject, ABC):
	"""Virtual base class for all game items.

	Attributes:
		item_type: The broad category this item falls under.
		durability: Remaining durability points (0 = broken).
		degrades: Whether the item loses durability on use.
		is_magical: True if the item counts as magical.
	"""

	def __init__(
		self,
		name: str,
		item_type: ItemType,
		durability: int,
		degrades: bool,
		is_magical: bool = False,
	) -> None:
		super().__init__(name)
		self.item_type: ItemType = item_type
		self.durability: int = durability
		self.degrades: bool = degrades
		self.is_magical: bool = is_magical

	def object_type(self) -> str:
		return "Item"

	def get_name(self) -> str:
		"""Return the display name of this item."""
		return self.name
