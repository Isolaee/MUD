"""Starting quest — talk to the shopkeeper to get a dagger and some clothes."""

from Objects.Items.Daggers.dagger import Dagger
from Objects.Rooms.room import Description
from Quests.objective import Objective, ObjectiveType
from Quests.quest import Quest
from Quests.reward import Reward, RewardType


class LookLikeADecentPerson(Quest):
	"""Starting quest where you will be provided a simple dagger and some clothes.

	The quest is to talk to the shopkeeper again, who will give you some advice
	on how to survive in the world. This quest is meant to introduce the player
	to the quest system and provide a simple task to complete.
	"""

	def __init__(self) -> None:
		super().__init__(
			name="Look Like a Decent Person",
			objectives=[
				Objective(
					description="Talk to the shopkeeper again.",
					objective_type=ObjectiveType.TALK_TO,
					target_name="Charles Willoby",
				),
			],
			rewards=[
				Reward(
					reward_type=RewardType.EXPERIENCE,
					description="A small amount of experience for being sociable.",
					value=10,
				),
				Reward(
					reward_type=RewardType.ITEM,
					description="A simple dagger to help you on your journey.",
					item=Dagger(
						name="Simple Dagger",
						reach=1,
						durability=100,
						degrades=False,
						attackBonus=1,
						onHitEffect=[],
					),
				),
			],
		)
		self.description = Description(
			short="Speak with the shopkeeper once more.",
			long=(
				"The shopkeeper in the market square asked you to come back "
				"and talk to him again. He seems to have something on his mind."
			),
		)
		self.completed_description = Description(
			short="The shopkeeper smiles warmly.",
			long=(
				'"Well done! You look like a decent person now. '
				"Here, take this dagger — you'll need it out there. "
				"And some clothes so you don't freeze to death.\""
			),
		)
