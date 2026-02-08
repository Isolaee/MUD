"""Demo quest — a simple 'talk to NPC again' quest for testing."""

from Objects.room import Description
from Quests.objective import Objective, ObjectiveType
from Quests.quest import Quest
from Quests.reward import Reward, RewardType


class DemoQuest(Quest):
	"""A trivial quest: talk to the quest-giver again.

	Used for development and testing of the quest system.
	"""

	def __init__(self) -> None:
		super().__init__(
			name="A Friendly Chat",
			objectives=[
				Objective(
					description="Talk to the old guide again.",
					objective_type=ObjectiveType.TALK_TO,
					target_name="Old Guide",
				),
			],
			rewards=[
				Reward(
					reward_type=RewardType.EXPERIENCE,
					description="A small amount of experience for being sociable.",
					value=10,
				),
			],
		)
		self.description = Description(
			short="Speak with the old guide once more.",
			long=(
				"The old guide in the intro room asked you to come back "
				"and talk to him again. He seems to have something on his mind."
			),
		)
