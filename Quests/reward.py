"""Quest reward definitions.

Rewards describe what the player receives upon turning in a quest.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from Objects.Items.item import Item


class RewardType(Enum):
	"""Categories of quest rewards."""

	EXPERIENCE = auto()
	ITEM = auto()
	CURRENCY = auto()
	REPUTATION = auto()
	UNLOCK = auto()


@dataclass
class Reward:
	"""A single reward granted on quest turn-in.

	Attributes:
		reward_type: What kind of reward this is.
		description: Human-readable text.
		value: Numeric value (XP amount, gold amount, etc.).
		item_name: If reward_type is ITEM, the name/uid of the item.
	"""

	reward_type: RewardType
	description: str
	value: int = 0
	item_name: str | None = None
	item: Item | None = None
