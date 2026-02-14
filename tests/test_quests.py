"""Tests for quest system — Quest, Objective, Reward."""

from Quests.objective import Objective, ObjectiveType
from Quests.quest import Quest, QuestStage, QuestStatus
from Quests.reward import Reward, RewardType


class ConcreteQuest(Quest):
	"""Minimal concrete Quest for testing (Quest is abstract)."""

	pass


def _make_objective(required=1, optional=False):
	return Objective(
		description="Test objective",
		objective_type=ObjectiveType.KILL,
		target_name="Goblin",
		required_count=required,
		is_optional=optional,
	)


def _make_reward():
	return Reward(
		reward_type=RewardType.EXPERIENCE,
		description="XP reward",
		value=50,
	)


class TestObjective:
	def test_starts_incomplete(self):
		obj = _make_objective(required=3)
		assert not obj.is_complete()
		assert obj.current_count == 0

	def test_advance(self):
		obj = _make_objective(required=3)
		obj.advance()
		assert obj.current_count == 1
		assert not obj.is_complete()

	def test_advance_to_completion(self):
		obj = _make_objective(required=2)
		obj.advance()
		obj.advance()
		assert obj.is_complete()

	def test_advance_caps_at_required(self):
		obj = _make_objective(required=1)
		obj.advance(5)
		assert obj.current_count == 1

	def test_advance_custom_amount(self):
		obj = _make_objective(required=10)
		obj.advance(5)
		assert obj.current_count == 5


class TestQuest:
	def test_starts_not_started(self):
		q = ConcreteQuest("Test Quest")
		assert q.status == QuestStatus.NOT_STARTED
		assert q.current_stage == QuestStage.STAGE_1

	def test_start(self):
		q = ConcreteQuest("Test Quest")
		q.start()
		assert q.status == QuestStatus.IN_PROGRESS

	def test_is_complete_no_objectives(self):
		q = ConcreteQuest("Empty Quest")
		assert q.is_complete()

	def test_is_complete_with_fulfilled_objective(self):
		obj = _make_objective(required=1)
		obj.advance()
		q = ConcreteQuest("Quest", objectives=[obj])
		assert q.is_complete()

	def test_is_not_complete_with_unfulfilled_objective(self):
		obj = _make_objective(required=3)
		q = ConcreteQuest("Quest", objectives=[obj])
		assert not q.is_complete()

	def test_optional_objective_not_required_for_completion(self):
		required = _make_objective(required=1)
		required.advance()
		optional = _make_objective(required=5, optional=True)
		q = ConcreteQuest("Quest", objectives=[required, optional])
		assert q.is_complete()

	def test_complete_only_when_objectives_done(self):
		obj = _make_objective(required=1)
		q = ConcreteQuest("Quest", objectives=[obj])
		q.start()
		q.complete()
		# Objectives not met, status should stay IN_PROGRESS
		assert q.status == QuestStatus.IN_PROGRESS

	def test_complete_succeeds_when_objectives_done(self):
		obj = _make_objective(required=1)
		obj.advance()
		q = ConcreteQuest("Quest", objectives=[obj])
		q.start()
		q.complete()
		assert q.status == QuestStatus.COMPLETED

	def test_fail(self):
		q = ConcreteQuest("Quest")
		q.start()
		q.fail()
		assert q.status == QuestStatus.FAILED

	def test_turn_in_returns_rewards(self):
		obj = _make_objective(required=1)
		obj.advance()
		reward = _make_reward()
		q = ConcreteQuest("Quest", objectives=[obj], rewards=[reward])
		q.start()
		q.complete()
		received = q.turn_in()
		assert len(received) == 1
		assert received[0].value == 50
		assert q.status == QuestStatus.TURNED_IN

	def test_turn_in_not_completed_returns_empty(self):
		q = ConcreteQuest("Quest")
		q.start()
		assert q.turn_in() == []

	def test_advance_stage(self):
		q = ConcreteQuest("Quest")
		assert q.current_stage == QuestStage.STAGE_1
		q.advance_stage()
		assert q.current_stage == QuestStage.STAGE_2
		q.advance_stage()
		assert q.current_stage == QuestStage.STAGE_3

	def test_advance_stage_caps_at_last(self):
		q = ConcreteQuest("Quest")
		for _ in range(10):
			q.advance_stage()
		assert q.current_stage == QuestStage.STAGE_5
