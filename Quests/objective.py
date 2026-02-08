"""Quest objective definitions.

Objectives are the individual tasks within a quest that must be
completed.  They track type, target, required count, and progress.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class ObjectiveType(Enum):
	"""Categories of things a player can be asked to do."""

	KILL = auto()
	COLLECT = auto()
	DELIVER = auto()
	TALK_TO = auto()
	EXPLORE = auto()
	ESCORT = auto()
	INTERACT = auto()


@dataclass
class Objective:
	"""A single task within a quest.

	Attributes:
		description: Human-readable text shown in the quest journal.
		objective_type: What kind of task this is.
		target_name: Name or uid of the target (enemy type, item, NPC, room).
		required_count: How many times the action must be performed.
		current_count: Progress so far.
		is_optional: If True, this objective is not required for completion.
	"""

	description: str
	objective_type: ObjectiveType
	target_name: str
	required_count: int = 1
	current_count: int = 0
	is_optional: bool = False

	def is_complete(self) -> bool:
		"""Return True if progress meets or exceeds the requirement."""
		return self.current_count >= self.required_count

	def advance(self, amount: int = 1) -> None:
		"""Increment progress, capping at required_count."""
		self.current_count = min(
			self.current_count + amount,
			self.required_count,
		)
