"""Keyboard input thread using msvcrt (Windows)."""

from __future__ import annotations

import msvcrt
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from UI.game_ui import GameUI

from UI.commands import dispatch


def input_loop(ui: GameUI) -> None:
	while ui.running:
		if msvcrt.kbhit():
			ch = msvcrt.getwch()
			if ch == "\r":
				dispatch(ui, ui.input_buffer)
				ui.input_buffer = ""
			elif ch == "\x08":
				ui.input_buffer = ui.input_buffer[:-1]
			elif ch == "\x1b":
				pass
			elif ch in ("\x00", "\xe0"):
				msvcrt.getwch()
			elif ch.isprintable():
				ui.input_buffer += ch
		else:
			time.sleep(0.02)
