"""Application engine — owns the main loop, console, and input thread.

The ``Application`` class is the top-level entry point for the TUI.
It takes an initial View, spawns the keyboard input thread, and runs
a Rich Live display loop until the view signals it should stop.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from rich.console import Console
from rich.live import Live

from UI.input_handler import InputHandler

if TYPE_CHECKING:
	from UI.viewsClass import View


class Application:
	"""Top-level application that runs a View in a Rich Live loop."""

	FPS = 60

	def __init__(self, initial_view: View) -> None:
		self._view = initial_view
		self._console = Console()

	def run(self) -> None:
		"""Start the input thread and render loop.  Blocks until quit."""
		handler = InputHandler(self._view)
		handler.start()

		with Live(
			self._view.build_layout(),
			console=self._console,
			refresh_per_second=self.FPS,
			screen=True,
		) as live:
			while self._view.running:
				live.update(self._view.build_layout())
				time.sleep(1 / self.FPS)

		self._console.clear()
		self._console.print("[bold]Thanks for playing! Goodbye.[/bold]")
