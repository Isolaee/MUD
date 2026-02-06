from Objects.Items import weapons
from Objects.room import Room, Description
from World.FirstTown import introTown

# -- rooms --

intro_room = Room("Intro")
intro_room.description = Description(
    short="Small intro room.",
    long=(
        "A intro room with a sword on the ground."
        " A doorway leads east."
    ),
)

room2 = Room("Room2")
room2.description = Description(
    short="A second room.",
    long="An empty stone room. The exit is west.",
)

intro_room.add_connection(room2)
intro_room.add_connection(introTown.square)
introTown.square.add_connection(intro_room)
room2.add_connection(intro_room)

# -- items --

intro_sword = weapons.Sword(
    name="Intro Sword", durability=100, degrades=True, is_magical=False
    )
intro_room.add_item(intro_sword)

# -- area entry point --

START_ROOM = intro_room
