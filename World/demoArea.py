"""Demo area — the starting zone used for development and testing.

Defines three interconnected rooms and a sample weapon.  This module
is imported by ``app.py`` and exposes ``START_ROOM`` as the player's
initial location.

Room layout::

            Town Square (introTown)
                  |
    Room 3 ---- Room Intro ---- Room 2
      |                            |
      +----------------------------+
"""

from Objects.character import NonPlayerCharacter, Race, CharacterSize
from Objects.Items.Swords.shortSword import ShortSword
from Objects.room import Room, Description, Direction
from Quests.demoQuest import DemoQuest
from World.FirstTown import introTown

# -- rooms --

intro_room = Room("Room Intro")
intro_room.description = Description(
	short="Small intro room.",
	long=("A intro room with a sword on the ground. A doorway leads east."),
)

room2 = Room("Room 2")
room2.description = Description(
	short="A second room.",
	long="An empty stone room. The exit is west.",
)

Room3 = Room("Room 3")
Room3.description = Description(short="Empty room.", long="Empty room that has two doors.")

# Wire up room connections (bidirectional)
intro_room.add_connection(room2, Direction.EAST)
intro_room.add_connection(introTown.square, Direction.NORTH)
intro_room.add_connection(Room3, Direction.NORTH_EAST)
Room3.add_connection(room2, Direction.SOUTH)

# -- items --

# Example short sword placed in the demo area
sword = ShortSword(
	name="Short Sword", durability=100, degrades=False, reach=1, is_magical=False, attackBonus=2, onHitEffect=[]
)
sword.description = Description(
	short="A basic short sword.",
	long="A basic short sword lies here, its blade gleaming with a dull sheen. It looks sturdy and reliable, perfect for a novice adventurer.",
)

intro_room.present_items.append(sword)

# -- NPCs --

demo_quest = DemoQuest()

guide = NonPlayerCharacter(
	name="Old Guide",
	has_enters_the_room=False,
	quest=demo_quest,
	current_hp=20,
	current_stamina=10,
	base_attack=1,
	race=Race.HUMAN,
	characterSize=CharacterSize.MEDIUM,
	inventory=[],
)
guide.description = Description(
	short="An old guide.",
	long="A weathered old man leans against the wall, eyes twinkling with quiet wisdom. He looks like he wants to talk.",
)

intro_room.present_characters.append(guide)

# -- area entry point --

START_ROOM = intro_room
