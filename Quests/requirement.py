"""Quest requirement types for gating quest acceptance."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from Objects.Characters.character import PlayerCharacter


class RequirementType(Enum):
	"""Types of conditions that can gate quest acceptance."""

	QUEST_COMPLETED = auto()  # A specific quest must be TURNED_IN
	LEVEL = auto()  # Player must be at least this level
	ITEM = auto()  # Player must have a specific item in inventory


@dataclass
class Requirement:
	"""A single condition that must be met before a quest can be accepted.

	Attributes:
		req_type: The kind of check to perform.
		description: Human-readable text (shown for public requirements).
		target: Identifier for the check — quest name, item name, etc.
		value: Numeric threshold (e.g. minimum level).
	"""

	req_type: RequirementType
	description: str
	target: str = ""
	value: int = 0

	def check(self, player: PlayerCharacter) -> bool:
		"""Return True if *player* satisfies this requirement."""
		if self.req_type == RequirementType.QUEST_COMPLETED:
			return any(q.name.lower() == self.target.lower() and q.status.name == "TURNED_IN" for q in player.quests)

		if self.req_type == RequirementType.LEVEL:
			return getattr(player, "level", 0) >= self.value

		if self.req_type == RequirementType.ITEM:
			return any(item.name.lower() == self.target.lower() for item in player.inventory)

		return False
