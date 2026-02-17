"""Keyboard input handler (Windows-only, msvcrt).

Runs in a daemon thread alongside the Rich Live render loop.
Reads individual key-presses via ``msvcrt.getwch()`` and either
appends printable characters to the shared input buffer or handles
special keys (Enter, Backspace, Escape, function keys).

Note: This module is Windows-specific.  A cross-platform alternative
would need ``curses``, ``readchar``, or similar.
"""

from __future__ import annotations

import msvcrt
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from UI.viewsClass import View


class InputHandler:
	"""Reads keystrokes in a daemon thread and feeds them to a View."""

	POLL_INTERVAL = 0.02  # seconds between polls when idle

	def __init__(self, view: View) -> None:
		self._view = view
		self._thread: threading.Thread | None = None

	def start(self) -> None:
		"""Spawn the daemon input thread."""
		self._thread = threading.Thread(target=self._loop, daemon=True)
		self._thread.start()

	def _get_active_view(self) -> View:
		"""Walk the next_view chain to find the leaf view."""
		v = self._view
		while v.next_view is not None:
			v = v.next_view
		return v

	def _loop(self) -> None:
		"""Poll the keyboard and dispatch to the view.

		Key handling:
		- Enter (\\r): dispatch the current buffer as a command and clear it.
		- Backspace (\\x08): delete the last character in the buffer.
		- Tab (\\t): trigger tab-completion on the active view.
		- Escape (\\x1b): ignored (reserved for future use).
		- Function / arrow keys (\\x00, \\xe0): consume the follow-up byte.
		- Printable characters: append to the input buffer.
		"""
		while self._view.running:
			if msvcrt.kbhit():
				ch = msvcrt.getwch()
				if ch == "\r":
					# Enter — submit the command
					active = self._get_active_view()
					self._view.handle_input(active.input_buffer)
					active = self._get_active_view()
					active.input_buffer = ""
				elif ch == "\x08":
					# Backspace
					active = self._get_active_view()
					active.input_buffer = active.input_buffer[:-1]
				elif ch == "\t":
					# Tab completion — delegated to the active view
					active = self._get_active_view()
					active.handle_tab()
				elif ch == "\x1b":
					pass
				elif ch in ("\x00", "\xe0"):
					key = msvcrt.getwch()
					active = self._get_active_view()
					if key == "H":  # Arrow UP
						active.scroll_events_up()
					elif key == "P":  # Arrow DOWN
						active.scroll_events_down()
				elif ch.isprintable():
					active = self._get_active_view()
					active.input_buffer += ch
			else:
				time.sleep(self.POLL_INTERVAL)
