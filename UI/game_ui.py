"""GameUI state and main game loop."""

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
	MAX_HISTORY = 50

	def __init__(self, start: Room) -> None:
		self.running = True
		self.input_buffer = ""
		self.current_room: Room = start
		self.event_history: list[str] = [
			"[dim]Welcome to the MUD! Type [bold]help[/bold] for commands.[/dim]",
		]
		dispatch(self, "look")

	def build_layout(self) -> Layout:
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

		layout["left"].update(make_event_history(self))
		layout["current_events"].update(make_current_events(self))
		layout["writing"].update(make_writing_interface(self))
		layout["map"].update(make_map(self.current_room))
		layout["stats"].update(make_stats())
		layout["inventory"].update(make_inventory(self))

		return layout


def main(start_room: Room) -> None:
	console = Console()
	ui = GameUI(start_room)

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
