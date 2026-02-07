from __future__ import annotations

from abc import ABC
from enum import Enum, auto

from Objects.game_object import GameObject


class ItemType(Enum):
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
	"""Virtual base class for all game items."""

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
