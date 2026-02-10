"""Character creation UI for the MUD game.

Uses a simple state machine to walk the player through choosing
a name and class before entering the game world.

Steps: name -> class -> confirm
"""

from rich.layout import Layout
from rich.text import Text

from Objects.character import Class
from UI.panels import CommandInputPanel
from UI.viewsClass import View


class CharacterCreationUI(View):
	"""Step-by-step character creation screen."""

	STEPS = ("name", "class", "confirm")

	def __init__(self) -> None:
		super().__init__()
		self.character_name: str = ""
		self.character_class: str = ""
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
		valid_names = [c.name for c in Class]
		if choice not in valid_names:
			self.error = f"Invalid class. Choose from: {', '.join(c.name.capitalize() for c in Class)}"
			return
		self.character_class = Class[choice]
		self.error = ""
		self.step = "confirm"

	def _handle_confirm(self, text: str) -> None:
		answer = text.lower()
		if answer in ("y", "yes"):
			from UI.in_game_ui.gameUI import GameUI
			from World.demoArea import START_ROOM

			self.transition_to(GameUI, START_ROOM)
		elif answer in ("n", "no"):
			self.character_name = ""
			self.character_class = ""
			self.error = ""
			self.step = "name"
		else:
			self.error = "Please type yes or no."

	# -- layout ------------------------------------------------------------

	def _prompt_text(self) -> str:
		"""Return the prompt / instructions for the current step."""
		if self.step == "name":
			return "Enter your character's name:"
		if self.step == "class":
			classes = ", ".join(c.name.capitalize() for c in Class)
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
