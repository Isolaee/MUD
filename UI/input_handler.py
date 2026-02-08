"""Keyboard input thread using msvcrt (Windows-only).

Runs in a daemon thread alongside the Rich Live render loop.
Reads individual key-presses via ``msvcrt.getwch()`` and either
appends printable characters to the shared input buffer or handles
special keys (Enter, Backspace, Escape, function keys).

Note: This module is Windows-specific.  A cross-platform alternative
would need ``curses``, ``readchar``, or similar.
"""

from __future__ import annotations

import msvcrt
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from UI.game_ui import GameUI

from UI.commands import dispatch
from UI.tab_completion import complete


def input_loop(ui: GameUI) -> None:
	"""Poll the keyboard and feed characters into the UI input buffer.

	Runs until ``ui.running`` becomes False.  Key handling:
	- Enter (\\r): dispatch the current buffer as a command and clear it.
	- Backspace (\\x08): delete the last character in the buffer.
	- Escape (\\x1b): ignored (reserved for future use).
	- Function / arrow keys (\\x00, \\xe0): consume the follow-up byte.
	- Printable characters: append to the input buffer.
	"""
	while ui.running:
		if msvcrt.kbhit():
			ch = msvcrt.getwch()
			if ch == "\r":
				# Enter — submit the command
				dispatch(ui, ui.input_buffer)
				ui.input_buffer = ""
			elif ch == "\x08":
				# Backspace — remove last character
				ui.input_buffer = ui.input_buffer[:-1]
			elif ch == "\t":
				# Tab — trigger tab-completion
				complete(ui)
			elif ch == "\x1b":
				# Escape — currently a no-op
				pass
			elif ch in ("\x00", "\xe0"):
				# Function / arrow key prefix — skip the scan code
				msvcrt.getwch()
			elif ch.isprintable():
				ui.input_buffer += ch
		else:
			# No key pressed — sleep briefly to avoid busy-waiting
			time.sleep(0.02)
