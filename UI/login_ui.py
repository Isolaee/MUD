"""Login and registration UI.

State machine flow:
    menu -> login_username -> login_password -> [success]
         -> register_username -> register_password -> register_confirm -> [success]

On success, transitions to MainMenuUI with the authenticated account_id.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

from rich.align import Align
from rich.layout import Layout
from rich.text import Text
from rich_pixels import Pixels

from UI.panels import CommandInputPanel
from UI.viewsClass import View

if TYPE_CHECKING:
	from server.world_manager import WorldManager

# Validation rules
MIN_USERNAME_LEN = 3
MIN_PASSWORD_LEN = 6
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")

_ASSETS = Path(__file__).resolve().parent.parent / "assets"
MAGE_ART = Pixels.from_image_path(_ASSETS / "Placeholder_mage.png", resize=(18, 14))
WARRIOR_ART = Pixels.from_image_path(_ASSETS / "Placeholder_warrior.png", resize=(18, 14))


class LoginUI(View):
	"""Login / registration screen shown on SSH connect."""

	def __init__(self, world_manager: WorldManager) -> None:
		super().__init__()
		self.world_manager = world_manager
		self.step: str = "menu"
		self.error: str = ""
		self.info: str = ""
		# Temporary state during login / registration
		self._username: str = ""
		self._password: str = ""

	# -- input handling -------------------------------------------------------

	def _handle_input(self, text: str) -> None:
		text = text.strip()
		if not text:
			return

		handler = {
			"menu": self._handle_menu,
			"login_username": self._handle_login_username,
			"login_password": self._handle_login_password,
			"register_username": self._handle_register_username,
			"register_password": self._handle_register_password,
			"register_confirm": self._handle_register_confirm,
		}.get(self.step)

		if handler:
			handler(text)

	def _handle_menu(self, text: str) -> None:
		if text.lower() == "login" or text.lower() == "log-in" or text == "1":
			self.step = "login_username"
			self.error = ""
			self.info = ""
		elif text.lower() == "register" or text == "2":
			self.step = "register_username"
			self.error = ""
			self.info = ""
		elif text.lower() == "quit" or text == "3":
			self.process.exit(0)
		else:
			self.error = "Please type Login, Register, or Quit."

	# -- login flow -----------------------------------------------------------

	def _handle_login_username(self, text: str) -> None:
		self._username = text
		self.error = ""
		self.step = "login_password"

	def _handle_login_password(self, text: str) -> None:
		from server.auth import verify_password
		from server.database import get_account

		account = get_account(self._username)
		if account is None or not verify_password(text, account["password_hash"]):
			self.error = "Invalid username or password."
			self._password = ""
			self.step = "login_username"
			return

		self._finish_auth(account["id"], account["username"])

	# -- registration flow ----------------------------------------------------

	def _handle_register_username(self, text: str) -> None:
		if len(text) < MIN_USERNAME_LEN:
			self.error = f"Username must be at least {MIN_USERNAME_LEN} characters."
			return
		if not USERNAME_PATTERN.match(text):
			self.error = "Username may only contain letters, digits, and underscores."
			return

		from server.database import get_account

		if get_account(text) is not None:
			self.error = "That username is already taken."
			return

		self._username = text
		self.error = ""
		self.step = "register_password"

	def _handle_register_password(self, text: str) -> None:
		if len(text) < MIN_PASSWORD_LEN:
			self.error = f"Password must be at least {MIN_PASSWORD_LEN} characters."
			return
		self._password = text
		self.error = ""
		self.step = "register_confirm"

	def _handle_register_confirm(self, text: str) -> None:
		if text != self._password:
			self.error = "Passwords do not match. Try again."
			self._password = ""
			self.step = "register_password"
			return

		from server.auth import hash_password
		from server.database import create_account

		try:
			account_id = create_account(self._username, hash_password(text))
		except sqlite3.IntegrityError:
			self.error = "That username is already taken."
			self.step = "register_username"
			return

		self._finish_auth(account_id, self._username)

	# -- transition -----------------------------------------------------------

	def _finish_auth(self, account_id: int, username: str) -> None:
		from UI.main_menu_ui import MainMenuUI

		self.transition_to(MainMenuUI, self.world_manager, account_id, username)

	# -- tab completion -------------------------------------------------------

	def _get_tab_candidates(self, partial: str) -> list[str]:
		if self.step == "menu":
			return [c for c in ("1", "2") if c.startswith(partial)]
		return []

	# -- layout ---------------------------------------------------------------

	def _prompt_text(self) -> str:
		if self.step == "menu":
			return (
				"[bold]Welcome to the MUD![/bold]\n\n"
				"  [cyan]Login[/cyan]\n\n"
				"  [cyan]Create Account[/cyan]\n\n"
				"  [cyan]Quit[/cyan]"
			)
		if self.step == "login_username":
			return "Username:"
		if self.step == "login_password":
			return "Password:"
		if self.step == "register_username":
			return "Choose a username (letters, digits, underscores):"
		if self.step == "register_password":
			return "Choose a password (min 6 characters):"
		if self.step == "register_confirm":
			return "Confirm your password:"
		return ""

	def _build_layout(self) -> Layout:
		layout = Layout()
		layout.split_column(
			Layout(name="header", size=3),
			Layout(name="body", ratio=1),
			Layout(name="footer", size=3),
		)

		layout["header"].update("[bold]MUD Login[/bold]")

		layout["body"].split_row(
			Layout(name="left_pad", ratio=1),
			Layout(name="left_art", size=20),
			Layout(name="main", size=30),
			Layout(name="right_art", size=20),
			Layout(name="right_pad", ratio=1),
		)

		layout["left_pad"].update("")
		layout["right_pad"].update("")
		layout["left_art"].update(Align.right(MAGE_ART, vertical="middle"))
		layout["right_art"].update(Align.left(WARRIOR_ART, vertical="middle"))

		body_parts = [self._prompt_text()]
		if self.error:
			body_parts.append(f"\n[red]{self.error}[/red]")
		if self.info:
			body_parts.append(f"\n[green]{self.info}[/green]")
		layout["main"].update(Align.center(Text.from_markup("\n".join(body_parts)), vertical="middle"))

		# Mask password input
		if self.step in ("login_password", "register_password", "register_confirm"):
			display_buffer = "*" * len(self.input_buffer)
		else:
			display_buffer = self.input_buffer
		layout["footer"].update(CommandInputPanel(display_buffer).build())

		return layout
