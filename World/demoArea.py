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

from Objects.Items.Swords.shortSword import ShortSword
from Objects.room import Room, Description, Direction
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

intro_room.present_items.append(sword)

# -- area entry point --

START_ROOM = intro_room
