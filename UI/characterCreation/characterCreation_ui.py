"""Character creation UI for the MUD game.

Uses a simple state machine to walk the player through choosing
a name and class before entering the game world.

Steps: name -> class -> confirm
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.layout import Layout
from rich.text import Text

from Objects.Characters.character import CharacterClassOptions
from Objects.Characters.characterClasses import get_all_classes
from Objects.Characters.characterRaces import get_all_races
from UI.panels import CommandInputPanel
from UI.viewsClass import View

if TYPE_CHECKING:
	from server.world_manager import WorldManager


class CharacterCreationUI(View):
	"""Step-by-step character creation screen."""

	STEPS = ("name", "class", "confirm")

	def __init__(self, world_manager: WorldManager, account_id: int) -> None:
		super().__init__()
		self.world_manager = world_manager
		self.account_id = account_id
		self.character_name: str = ""
		self.character_class: CharacterClassOptions | None = None
		self.step: str = "name"
		self.error: str = ""

	# -- input handling (called from View.handle_input) --------------------

	def _handle_input(self, text: str) -> None:
		"""Route submitted text to the handler for the current step."""
		text = text.strip()
		if not text:
			return

		if self.step == "name":
			self._handle_name(text)
		elif self.step == "class":
			self._handle_class(text)
		elif self.step == "confirm":
			self._handle_confirm(text)

	def _handle_name(self, text: str) -> None:
		if len(text) < 2:
			self.error = "Name must be at least 2 characters."
			return
		self.character_name = text
		self.error = ""
		self.step = "class"

	def _handle_class(self, text: str) -> None:
		choice = text.upper()
		valid_names = [c.name for c in CharacterClassOptions]
		if choice not in valid_names:
			self.error = f"Invalid class. Choose from: {', '.join(n.capitalize() for n in valid_names)}"
			return
		self.character_class = CharacterClassOptions[choice]
		self.error = ""
		self.step = "confirm"

	def _handle_confirm(self, text: str) -> None:
		answer = text.lower()
		if answer in ("y", "yes"):
			self._create_and_enter_game()
		elif answer in ("n", "no"):
			self.character_name = ""
			self.character_class = None
			self.error = ""
			self.step = "name"
		else:
			self.error = "Please type yes or no."

	def _create_and_enter_game(self) -> None:
		"""Save the new character to DB, build a PlayerCharacter, and enter the game."""
		from Objects.Characters.character import CharacterRaceOptions, PlayerCharacter
		from server.database import create_character_record
		from UI.in_game_ui.gameUI import GameUI

		# Calculate stats with class and race modifiers
		race = CharacterRaceOptions.HUMAN  # default for now
		class_instance = get_all_classes()[self.character_class.name]()
		race_instance = get_all_races()[race.name]()
		class_mods = class_instance.stat_modifiers
		race_mods = race_instance.stat_modifiers

		base_hp = 100
		base_stamina = 100
		base_attack = 10

		hp = base_hp + class_mods.hp + race_mods.hp
		stamina = base_stamina + class_mods.stamina + race_mods.stamina
		attack = base_attack + class_mods.attack + race_mods.attack

		# Save to database
		character_id = create_character_record(
			self.account_id,
			self.character_name,
			self.character_class.name,
			race.name,
			hp,
			stamina,
			attack,
		)

		# Build in-memory PlayerCharacter
		player = PlayerCharacter(
			current_hp=hp,
			current_stamina=stamina,
			base_attack=attack,
			race=race,
			character_class=self.character_class,
			characterSize=race_instance.size,
			inventory=[],
			name=self.character_name,
		)

		self.transition_to(
			GameUI,
			self.world_manager,
			player,
			character_id,
			self.account_id,
		)

	# -- tab completion ----------------------------------------------------

	def _get_tab_candidates(self, partial: str) -> list[str]:
		"""Return completion candidates based on the current step."""
		if self.step == "class":
			return [c.name.capitalize() for c in CharacterClassOptions if c.name.lower().startswith(partial)]
		if self.step == "confirm":
			return [w for w in ("yes", "no") if w.startswith(partial)]
		return []

	# -- layout ------------------------------------------------------------

	def _prompt_text(self) -> str:
		"""Return the prompt / instructions for the current step."""
		if self.step == "name":
			return "Enter your character's name:"
		if self.step == "class":
			classes = ", ".join(c.name.capitalize() for c in CharacterClassOptions)
			return f"Choose a class ({classes}):"
		return (
			f"Name:  [bold]{self.character_name}[/bold]\n"
			f"Class: [bold]{self.character_class.name.capitalize()}[/bold]\n\n"
			"Is this correct? (yes / no)"
		)

	def _build_layout(self) -> Layout:
		"""Build the Rich layout for the character creation screen."""
		layout = Layout()
		layout.split_column(
			Layout(name="header", size=3),
			Layout(name="body", ratio=1),
			Layout(name="footer", size=3),
		)

		layout["header"].update("[bold]Character Creation[/bold]")

		body_parts = [self._prompt_text()]
		if self.error:
			body_parts.append(f"\n[red]{self.error}[/red]")
		layout["body"].update(Text.from_markup("\n".join(body_parts)))

		layout["footer"].update(CommandInputPanel(self.input_buffer).build())
		return layout
