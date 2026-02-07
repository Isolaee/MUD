from Objects.Items.Swords.shortSword import ShortSword
from Objects.room import Room, Description, Direction
from World.FirstTown import introTown

# -- rooms --

intro_room = Room("Intro")
intro_room.description = Description(
	short="Small intro room.",
	long=("A intro room with a sword on the ground. A doorway leads east."),
)

room2 = Room("Room2")
room2.description = Description(
	short="A second room.",
	long="An empty stone room. The exit is west.",
)

Room3 = Room("Room 3")
Room3.description = Description(short="Empty room.", long="Empty room that has two doors.")

intro_room.add_connection(room2, Direction.EAST)
intro_room.add_connection(introTown.square, Direction.NORTH)
intro_room.add_connection(Room3, Direction.NORTH_EAST)
Room3.add_connection(room2, Direction.SOUTH)

# -- items --

# Example short sword
sword = ShortSword(
	name="Short Sword", durability=100, degrades=False, reach=1, is_magical=False, attackBonus=2, onHitEffect=[]
)

# -- area entry point --

START_ROOM = intro_room
