"""GameUI state container and main game loop.

GameUI holds all mutable session state (current room, input buffer,
event history) and owns the Rich layout that is redrawn every frame.

The ``main()`` function is the application entry point: it creates
the UI, spawns a keyboard-input thread, and runs a Rich Live display
at 60 FPS until the player quits.

Layout structure::

    +-----------+---------------------+----------+
    |  Event    |   Current Events    |   Map    |
    |  History  |                     |----------|
    |           |                     |  Stats   |
    |           |---------------------|----------|
    |           |  Command Input      | Inventory|
    +-----------+---------------------+----------+
"""

import threading
import time

from rich.console import Console
from UI.input_handler import input_loop
from rich.layout import Layout
from rich.live import Live
from UI.characterCreation.characterCreation_ui import CharacterCreationUI


def main(currentView: Layout) -> None:
	"""Game entry point — run the TUI until the player quits.

	Args:
		start_room: The room the player begins in.
	"""
	console = Console()
	# ui = GameUI(currentView)
	ui = CharacterCreationUI()

	# Keyboard input runs in a daemon thread so it dies with the main thread
	thread = threading.Thread(target=input_loop, args=(ui,), daemon=True)
	thread.start()

	with Live(
		ui.build_layout(),
		console=console,
		refresh_per_second=60,
		screen=True,
	) as live:
		while ui.running:
			live.update(ui.build_layout())
			time.sleep(0.1)

	console.clear()
	console.print("[bold]Thanks for playing! Goodbye.[/bold]")
