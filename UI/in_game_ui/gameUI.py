"""In-game UI state container and layout builder.

GameUI holds all mutable session state (current room, input buffer,
event history) and owns the Rich layout that is redrawn every frame.

Layout structure::

    +-----------+---------------------+----------+
    |  Event    |   Current Events    |   Map    |
    |  History  |                     |----------|
    |           |                     |  Stats   |
    |           |---------------------|----------|
    |           |  Command Input      | Inventory|
    +-----------+---------------------+----------+
"""

from rich.layout import Layout

from Objects.room import Room
from UI.commands import CommandDispatcher
from UI.map_renderer import MapRenderer
from UI.panels import (
	CommandInputPanel,
	CurrentEventsPanel,
	EventHistoryPanel,
	InventoryPanel,
	StatsPanel,
)
from UI.viewsClass import View


class GameUI(View):
	"""Central state object shared between the render loop and input thread.

	Attributes:
		MAX_HISTORY: Maximum number of event-log entries kept in memory.
		current_room: The room the player is currently in.
		event_history: Chronological list of Rich-markup log messages.
		completion_state: Tab-completion state (used by TabCompleter).
	"""

	MAX_HISTORY = 60

	def __init__(self, starting_room: Room) -> None:
		super().__init__()
		self.current_room: Room = starting_room
		self.completion_state = None
		self.event_history: list[str] = [
			"[dim]Welcome to the MUD! Type [bold]help[/bold] for commands.[/dim]",
		]
		self._dispatcher = CommandDispatcher()
		# Show the starting room description immediately
		self._dispatcher.dispatch(self, "look")

	def _handle_input(self, text: str) -> None:
		"""Dispatch command through the command dispatcher."""
		self._dispatcher.dispatch(self, text)

	def _build_layout(self) -> Layout:
		"""Construct the full Rich Layout for one frame."""
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

		layout["left"].update(EventHistoryPanel(self.event_history).build())
		layout["current_events"].update(CurrentEventsPanel(self.current_room).build())
		layout["writing"].update(CommandInputPanel(self.input_buffer).build())
		layout["map"].update(MapRenderer(self.current_room).build())
		layout["stats"].update(StatsPanel().build())
		layout["inventory"].update(InventoryPanel(self.current_room.present_items).build())

		return layout
