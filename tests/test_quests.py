"""Tests for quest system — Quest, Objective, Reward, Requirement."""

from Quests.objective import Objective, ObjectiveType
from Quests.quest import Quest, QuestStage, QuestStatus
from Quests.requirement import Requirement, RequirementType
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


# ---------------------------------------------------------------------------
# Helpers for requirement tests
# ---------------------------------------------------------------------------


class _MockPlayer:
	"""Lightweight stand-in for PlayerCharacter in requirement tests."""

	def __init__(self, level=1, quests=None, inventory=None):
		self.level = level
		self.quests = quests or []
		self.inventory = inventory or []


class _MockItem:
	def __init__(self, name: str):
		self.name = name


def _make_requirement(req_type, description="req", target="", value=0):
	return Requirement(
		req_type=req_type,
		description=description,
		target=target,
		value=value,
	)


# ---------------------------------------------------------------------------
# Requirement.check tests
# ---------------------------------------------------------------------------


class TestRequirement:
	def test_level_requirement_met(self):
		req = _make_requirement(RequirementType.LEVEL, value=5)
		player = _MockPlayer(level=5)
		assert req.check(player)

	def test_level_requirement_not_met(self):
		req = _make_requirement(RequirementType.LEVEL, value=10)
		player = _MockPlayer(level=3)
		assert not req.check(player)

	def test_level_defaults_to_zero_when_missing(self):
		req = _make_requirement(RequirementType.LEVEL, value=1)
		player = _MockPlayer()
		del player.level
		assert not req.check(player)

	def test_quest_completed_requirement_met(self):
		completed_quest = ConcreteQuest("First Steps")
		completed_quest.status = QuestStatus.TURNED_IN
		req = _make_requirement(RequirementType.QUEST_COMPLETED, target="First Steps")
		player = _MockPlayer(quests=[completed_quest])
		assert req.check(player)

	def test_quest_completed_requirement_not_met(self):
		in_progress = ConcreteQuest("First Steps")
		in_progress.status = QuestStatus.IN_PROGRESS
		req = _make_requirement(RequirementType.QUEST_COMPLETED, target="First Steps")
		player = _MockPlayer(quests=[in_progress])
		assert not req.check(player)

	def test_quest_completed_case_insensitive(self):
		q = ConcreteQuest("First Steps")
		q.status = QuestStatus.TURNED_IN
		req = _make_requirement(RequirementType.QUEST_COMPLETED, target="first steps")
		player = _MockPlayer(quests=[q])
		assert req.check(player)

	def test_item_requirement_met(self):
		req = _make_requirement(RequirementType.ITEM, target="Iron Key")
		player = _MockPlayer(inventory=[_MockItem("Iron Key")])
		assert req.check(player)

	def test_item_requirement_not_met(self):
		req = _make_requirement(RequirementType.ITEM, target="Iron Key")
		player = _MockPlayer(inventory=[])
		assert not req.check(player)

	def test_item_requirement_case_insensitive(self):
		req = _make_requirement(RequirementType.ITEM, target="iron key")
		player = _MockPlayer(inventory=[_MockItem("Iron Key")])
		assert req.check(player)


# ---------------------------------------------------------------------------
# Quest.can_accept tests
# ---------------------------------------------------------------------------


class TestCanAccept:
	def test_no_requirements_can_accept(self):
		q = ConcreteQuest("Open Quest")
		player = _MockPlayer()
		can, unmet = q.can_accept(player)
		assert can
		assert unmet == []

	def test_public_requirement_met(self):
		req = _make_requirement(RequirementType.LEVEL, description="Level 5", value=5)
		q = ConcreteQuest("Quest", public_requirements=[req])
		player = _MockPlayer(level=10)
		can, unmet = q.can_accept(player)
		assert can
		assert unmet == []

	def test_public_requirement_not_met(self):
		req = _make_requirement(RequirementType.LEVEL, description="Reach level 5", value=5)
		q = ConcreteQuest("Quest", public_requirements=[req])
		player = _MockPlayer(level=2)
		can, unmet = q.can_accept(player)
		assert not can
		assert unmet == ["Reach level 5"]

	def test_hidden_requirement_not_met_no_descriptions(self):
		req = _make_requirement(RequirementType.LEVEL, description="secret", value=99)
		q = ConcreteQuest("Quest", hidden_requirements=[req])
		player = _MockPlayer(level=1)
		can, unmet = q.can_accept(player)
		assert not can
		assert unmet == []  # hidden requirements don't expose descriptions

	def test_hidden_requirement_met(self):
		req = _make_requirement(RequirementType.LEVEL, value=1)
		q = ConcreteQuest("Quest", hidden_requirements=[req])
		player = _MockPlayer(level=5)
		can, unmet = q.can_accept(player)
		assert can

	def test_mixed_requirements_all_met(self):
		pub = _make_requirement(RequirementType.LEVEL, description="Level 3", value=3)
		hid = _make_requirement(RequirementType.ITEM, target="Key")
		q = ConcreteQuest("Quest", public_requirements=[pub], hidden_requirements=[hid])
		player = _MockPlayer(level=5, inventory=[_MockItem("Key")])
		can, unmet = q.can_accept(player)
		assert can

	def test_mixed_requirements_public_fails(self):
		pub = _make_requirement(RequirementType.LEVEL, description="Level 10", value=10)
		hid = _make_requirement(RequirementType.ITEM, target="Key")
		q = ConcreteQuest("Quest", public_requirements=[pub], hidden_requirements=[hid])
		player = _MockPlayer(level=5, inventory=[_MockItem("Key")])
		can, unmet = q.can_accept(player)
		assert not can
		assert unmet == ["Level 10"]
