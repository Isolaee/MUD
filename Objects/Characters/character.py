"""Character hierarchy for player and non-player characters.

Defines the abstract Character base and two concrete subclasses:
- PlayerCharacter: controlled by a human player.
- NonPlayerCharacter: controlled by game logic / AI.

Currently minimal — stats, abilities, and behaviour will be
added as the game evolves.
"""

from __future__ import annotations

from abc import ABC
from enum import Enum, auto
from typing import TYPE_CHECKING

from Objects.Characters.characterClasses import get_all_classes
from Objects.Characters.characterRaces import CharacterSize, get_all_races
from Objects.game_object import GameObject

if TYPE_CHECKING:
	from Objects.Items.weapons import Weapon
	from Objects.Rooms.room import Room
	from Quests.quest import Quest


class CharacterType(Enum):
	PLAYER = auto()
	NPC = auto()


CharacterRaceOptions = Enum(
	"CharacterRaceOptions",
	{name: auto() for name in get_all_races()},
)


# Auto-generated from CharacterClass subclasses in characterClasses.py
CharacterClassOptions = Enum(
	"CharacterClassOptions",
	{name: auto() for name in get_all_classes()},
)


class Character(GameObject, ABC):
	"""Virtual base class for all characters.

	Inherits identity, properties, and tags from GameObject.
	Future additions: health, stats, equipment slots, etc.
	"""

	def __init__(self, name: str) -> None:
		super().__init__(name)


class PlayerCharacter(Character):
	"""A player-controlled character.

	Represents the human player's avatar in the game world.
	"""

	def __init__(
		self,
		current_hp: int,
		current_stamina: int,
		base_attack: int,
		race: CharacterRaceOptions,
		character_class: CharacterClassOptions,
		characterSize: CharacterSize,
		inventory: list,
		**kwargs,
	) -> None:
		super().__init__(**kwargs)
		self.hp = current_hp
		self.max_hp = current_hp
		self.stamina = current_stamina
		self.max_stamina = current_stamina
		self.base_attack = base_attack  # Do we want to derive base attack value from race? Base attack would not be defined on creation but calculated on demand based on race, size and items.
		self.race = race
		self.character_class = character_class
		self.size = characterSize
		self.inventory = inventory
		self.equipped_weapon: Weapon | None = None
		self.is_knocked_out: bool = False
		self.visited_rooms: set[Room] = set()

	def create_character(
		self, name: str, race: CharacterRaceOptions, character_class: CharacterClassOptions
	) -> Character:
		"""Create a new character with the given parameters.

		Base stats are adjusted additively by the chosen character class modifiers.
		"""
		# Resolve class and race instances for their modifiers
		class_instance = get_all_classes()[character_class.name]()
		race_instance = get_all_races()[race.name]()
		class_mods = class_instance.stat_modifiers
		race_mods = race_instance.stat_modifiers

		base_hp = 100
		base_stamina = 100
		base_attack = 10

		return PlayerCharacter(
			current_hp=base_hp + class_mods.hp + race_mods.hp,
			current_stamina=base_stamina + class_mods.stamina + race_mods.stamina,
			base_attack=base_attack + class_mods.attack + race_mods.attack,
			race=race,
			character_class=character_class,
			characterSize=race_instance.size,
			inventory=[],
			name=name,
		)

	def visit_room(self, room: Room) -> None:
		"""Mark a room as visited."""
		self.visited_rooms.add(room)

	def has_visited(self, room: Room) -> bool:
		"""Check whether the player has visited a room."""
		return room in self.visited_rooms

	def object_type(self) -> CharacterType:
		return CharacterType.PLAYER


class NonPlayerCharacter(PlayerCharacter):
	"""An NPC (non-player character).

	Represents characters controlled by game logic, such as
	merchants, quest-givers, or enemies.
	"""

	def __init__(self, has_enters_the_room: bool, quest: Quest | None = None, **kwargs) -> None:
		super().__init__(**kwargs)
		self.has_enters_the_room = has_enters_the_room
		self.quest = quest

	def object_type(self) -> CharacterType:
		return CharacterType.NPC
