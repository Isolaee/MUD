"""Quest base class and status/stage enums.

Quests are GameObjects that represent tasks a player can accept,
progress through, and complete.  Each quest has a status, a list
of stages, objectives, rewards, and requirements.
"""

from __future__ import annotations

from abc import ABC
from enum import Enum, auto
from typing import TYPE_CHECKING

from Objects.game_object import GameObject
from Objects.Rooms.room import Description
from Quests.objective import Objective
from Quests.requirement import Requirement
from Quests.reward import Reward

if TYPE_CHECKING:
	from Objects.Characters.character import PlayerCharacter


class QuestStatus(Enum):
	"""Tracks where the player stands with a quest."""

	NOT_STARTED = auto()
	IN_PROGRESS = auto()
	COMPLETED = auto()
	FAILED = auto()
	TURNED_IN = auto()


class QuestStage(Enum):
	"""Generic stages for multi-part quests.

	Concrete quests can define their own stage enums if needed.
	"""

	STAGE_1 = auto()
	STAGE_2 = auto()
	STAGE_3 = auto()
	STAGE_4 = auto()
	STAGE_5 = auto()


class Quest(GameObject, ABC):
	"""Virtual base class for all quests.

	Inherits identity, properties, and tags from GameObject.

	Attributes:
		description: Short/long text for quest journal display.
		status: Current quest status.
		current_stage: Which stage the player is on.
		objectives: List of objectives to complete.
		rewards: What the player receives on completion.
		public_requirements: Conditions shown to the player that must be met.
		hidden_requirements: Conditions not shown but still enforced.
		is_repeatable: Whether the quest can be taken again.
	"""

	def __init__(
		self,
		name: str,
		objectives: list[Objective] | None = None,
		rewards: list[Reward] | None = None,
		public_requirements: list[Requirement] | None = None,
		hidden_requirements: list[Requirement] | None = None,
		is_repeatable: bool = False,
	) -> None:
		super().__init__(name)
		self.description: Description | None = None
		self.completed_description: Description | None = None
		self.status: QuestStatus = QuestStatus.NOT_STARTED
		self.current_stage: QuestStage = QuestStage.STAGE_1
		self.objectives: list[Objective] = objectives or []
		self.rewards: list[Reward] = rewards or []
		self.public_requirements: list[Requirement] = public_requirements or []
		self.hidden_requirements: list[Requirement] = hidden_requirements or []
		self.is_repeatable: bool = is_repeatable

	def object_type(self) -> str:
		return "Quest"

	def can_accept(self, player: PlayerCharacter) -> tuple[bool, list[str]]:
		"""Check whether *player* meets all requirements for this quest.

		Returns (True, []) when all requirements are satisfied.
		Returns (False, [descriptions…]) when requirements are unmet —
		only *public* requirement descriptions are included.
		"""
		unmet_public: list[str] = []
		has_hidden_fail = False

		for req in self.public_requirements:
			if not req.check(player):
				unmet_public.append(req.description)

		for req in self.hidden_requirements:
			if not req.check(player):
				has_hidden_fail = True
				break

		if unmet_public or has_hidden_fail:
			return False, unmet_public
		return True, []

	def is_complete(self) -> bool:
		"""Return True if all non-optional objectives are satisfied."""
		return all(obj.is_complete() for obj in self.objectives if not obj.is_optional)

	def advance_stage(self) -> None:
		"""Move to the next QuestStage, if one exists."""
		stages = list(QuestStage)
		idx = stages.index(self.current_stage)
		if idx + 1 < len(stages):
			self.current_stage = stages[idx + 1]

	def start(self) -> None:
		"""Mark the quest as in progress."""
		self.status = QuestStatus.IN_PROGRESS

	def complete(self) -> None:
		"""Mark the quest as completed (rewards not yet collected)."""
		if self.is_complete():
			self.status = QuestStatus.COMPLETED

	def fail(self) -> None:
		"""Mark the quest as failed."""
		self.status = QuestStatus.FAILED

	def turn_in(self) -> list[Reward]:
		"""Collect rewards and mark as turned in."""
		if self.status == QuestStatus.COMPLETED:
			self.status = QuestStatus.TURNED_IN
			return self.rewards
		return []
