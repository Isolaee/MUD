from Objects.Characters.character import CharacterClassOptions, CharacterRaceOptions, NonPlayerCharacter
from Objects.Characters.characterRaces import CharacterSize
from Objects.Rooms.room import Room, Description, Direction
from Quests.StartingTown.look_like_a_decent_person import LookLikeADecentPerson

# -- rooms --

roadside = Room("Roadside")
roadside.description = Description(
	short="A short road with a gutter.",
	long=(
		"A short stretch of road runs here, bordered by a shallow gutter. The air is fresh with the scent of nearby greenery."
	),
)
roadside.first_time_visited_text = "You wake up from the gutter, it's dawn and your head is pounding. You have some fussy memories of a night of drinking, but nothing concrete. You money pouch is gone and you are wearing just a dirty shirty. You are alive, but not well. What ever you had in your life is gone, time to start a new one."

road_to_market = Room("CobbleStone Road")
road_to_market.description = Description(
	short="Long road to the market.",
	long="A long road stretches out before you, leading towards the bustling market in the distance. The sound of merchants calling out their wares and the scent of fresh bread waft through the air.",
)
road_to_market.on_enter_text = "[dim]Your footsteps echo off the cold stone walls.[/dim]. You see some dark figures lurking in the shadows, but they don't seem to notice you."

marketSquare = Room("Market Square")
marketSquare.description = Description(short="Empty room.", long="Empty room that has two doors.")
marketSquare.on_enter_action = lambda player, room: [f"[yellow]A draft chills {player.name} to the bone.[/yellow]"]

# Wire up room connections (bidirectional)
roadside.add_connection(road_to_market, Direction.EAST)
road_to_market.add_connection(marketSquare, Direction.EAST)

# -- items --

# # Example short sword placed in the demo area
# sword = ShortSword(
# 	name="Short Sword", durability=100, degrades=False, reach=1, is_magical=False, attackBonus=2, onHitEffect=[]
# )
# sword.description = Description(
# 	short="A basic short sword.",
# 	long="A basic short sword lies here, its blade gleaming with a dull sheen. It looks sturdy and reliable, perfect for a novice adventurer.",
# )


# -- NPCs --

# 1st quest
look_like_a_decent_person = LookLikeADecentPerson()

shopkeeper = NonPlayerCharacter(
	name="Charles Willoby",
	has_enters_the_room=True,
	quest=look_like_a_decent_person,
	current_hp=50,
	current_stamina=30,
	base_attack=5,
	race=CharacterRaceOptions.HUMAN,
	character_class=CharacterClassOptions.ROGUE,
	characterSize=CharacterSize.MEDIUM,
	inventory=[],
)

shopkeeper.description = Description(
	short="A friendly shopkeeper.",
	long="A friendly shopkeeper stands behind a food stall, his eyes twinkling with mischief and kindness. He seems approachable and eager to help.",
)
marketSquare.add_character(shopkeeper)

# demo_quest = DemoQuest()

# guide = NonPlayerCharacter(
# 	name="Old Guide",
# 	has_enters_the_room=False,
# 	quest=demo_quest,
# 	current_hp=20,
# 	current_stamina=10,
# 	base_attack=1,
# 	race=CharacterRaceOptions.HUMAN,
# 	character_class=CharacterClassOptions.WARRIOR,
# 	characterSize=CharacterSize.MEDIUM,
# 	inventory=[],
# )
# guide.description = Description(
# 	short="An old guide.",
# 	long="A weathered old man leans against the wall, eyes twinkling with quiet wisdom. He looks like he wants to talk.",
# )


# -- area entry point --

START_ROOM = roadside
