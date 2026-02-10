from rich.layout import Layout

from Objects.room import Room
from UI.commands import dispatch
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

	MAX_HISTORY = 60

	def __init__(self, startingRoom: Room) -> None:
		self.running = True
		self.input_buffer = ""
		self.current_room: Room = startingRoom
		self.completion_state = None  # CompletionState | None — used by tab_completion
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
