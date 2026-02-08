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
from rich.layout import Layout
from rich.live import Live

from Objects.room import Room
from UI.commands import dispatch
from UI.input_handler import input_loop
from UI.map_renderer import make_map
from UI.panels import (
	make_current_events,
	make_event_history,
	make_inventory,
	make_stats,
	make_writing_interface,
)


class GameUI:
	"""Central state object shared between the render loop and input thread.

	Attributes:
		MAX_HISTORY: Maximum number of event-log entries kept in memory.
		running: Set to False to stop the game loop.
		input_buffer: Characters the player has typed so far.
		current_room: The room the player is currently in.
		event_history: Chronological list of Rich-markup log messages.
	"""

	MAX_HISTORY = 50

	def __init__(self, start: Room) -> None:
		self.running = True
		self.input_buffer = ""
		self.current_room: Room = start
		self.event_history: list[str] = [
			"[dim]Welcome to the MUD! Type [bold]help[/bold] for commands.[/dim]",
		]
		# Show the starting room description immediately
		dispatch(self, "look")

	def build_layout(self) -> Layout:
		"""Construct the full Rich Layout for one frame.

		Returns a three-column layout: event history on the left,
		current events + command input in the centre, and map /
		stats / inventory stacked on the right.
		"""
		layout = Layout()
		layout.split_row(
			Layout(name="left", ratio=1),
			Layout(name="middle", ratio=3),
			Layout(name="right", ratio=1),
		)
		layout["middle"].split_column(
			Layout(name="current_events", ratio=1),
			Layout(name="writing", size=3),
		)
		layout["right"].split_column(
			Layout(name="map", ratio=1),
			Layout(name="stats", ratio=1),
			Layout(name="inventory", ratio=1),
		)

		# Populate each panel
		layout["left"].update(make_event_history(self))
		layout["current_events"].update(make_current_events(self))
		layout["writing"].update(make_writing_interface(self))
		layout["map"].update(make_map(self.current_room))
		layout["stats"].update(make_stats())
		layout["inventory"].update(make_inventory(self))

		return layout


def main(start_room: Room) -> None:
	"""Game entry point — run the TUI until the player quits.

	Args:
		start_room: The room the player begins in.
	"""
	console = Console()
	ui = GameUI(start_room)

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
