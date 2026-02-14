"""Main menu UI — character selection after login.

Shows the player's existing characters and options to create a new one
or log out.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.layout import Layout
from rich.text import Text

from UI.panels import CommandInputPanel
from UI.viewsClass import View

if TYPE_CHECKING:
	from server.world_manager import WorldManager


class MainMenuUI(View):
	"""Character selection screen shown after successful login."""

	def __init__(self, world_manager: WorldManager, account_id: int, username: str) -> None:
		super().__init__()
		self.world_manager = world_manager
		self.account_id = account_id
		self.username = username
		self.error: str = ""
		self._characters: list = []
		self._refresh_characters()

	def _refresh_characters(self) -> None:
		from server.database import get_characters_for_account

		self._characters = get_characters_for_account(self.account_id)

	# -- input handling -------------------------------------------------------

	def _handle_input(self, text: str) -> None:
		text = text.strip().lower()
		if not text:
			return

		if text == "n":
			self._start_character_creation()
			return

		if text == "q":
			from UI.login_ui import LoginUI

			self.transition_to(LoginUI, self.world_manager)
			return

		# Try to parse as a number (character selection)
		try:
			index = int(text) - 1
		except ValueError:
			self.error = "Invalid choice. Enter a number, N, or Q."
			return

		if 0 <= index < len(self._characters):
			self._select_character(self._characters[index])
		else:
			self.error = "Invalid character number."

	def _start_character_creation(self) -> None:
		from UI.characterCreation.characterCreation_ui import CharacterCreationUI

		self.transition_to(CharacterCreationUI, self.world_manager, self.account_id)

	def _select_character(self, char_row) -> None:
		from server.database import load_player_character
		from UI.in_game_ui.gameUI import GameUI

		player = load_player_character(char_row)
		character_id = char_row["id"]
		self.transition_to(
			GameUI,
			self.world_manager,
			player,
			character_id,
			self.account_id,
		)

	# -- tab completion -------------------------------------------------------

	def _get_tab_candidates(self, partial: str) -> list[str]:
		options = [str(i + 1) for i in range(len(self._characters))] + ["n", "q"]
		return [o for o in options if o.startswith(partial)]

	# -- layout ---------------------------------------------------------------

	def _build_layout(self) -> Layout:
		layout = Layout()
		layout.split_column(
			Layout(name="header", size=3),
			Layout(name="body", ratio=1),
			Layout(name="footer", size=3),
		)

		layout["header"].update(f"[bold]Welcome, {self.username}![/bold]")

		parts = ["[bold]Your characters:[/bold]\n"]
		if self._characters:
			for i, char in enumerate(self._characters):
				cls = char["character_class"].capitalize()
				parts.append(f"  [cyan]{i + 1})[/cyan] {char['name']} ({cls})")
		else:
			parts.append("  [dim]No characters yet.[/dim]")

		parts.append("")
		parts.append("  [cyan]N)[/cyan] Create new character")
		parts.append("  [cyan]Q)[/cyan] Logout")
		parts.append("\nChoose an option:")

		if self.error:
			parts.append(f"\n[red]{self.error}[/red]")

		layout["body"].update(Text.from_markup("\n".join(parts)))
		layout["footer"].update(CommandInputPanel(self.input_buffer).build())

		return layout
