from Objects.item import Item, ItemType
from Objects.room import Room, Description


class SimpleItem(Item):
    def __init__(
        self,
        name: str,
        item_type: ItemType,
        is_magical: bool = False,
    ) -> None:
        super().__init__(name, item_type, is_magical)

    def object_type(self) -> str:
        return "SimpleItem"


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
room2.add_connection(intro_room)

# -- items --

intro_sword = SimpleItem(
    "Intro Sword", ItemType.WEAPONS
)
intro_room.add_item(intro_sword)

# -- area entry point --

START_ROOM = intro_room
