"""In-game UI state container and layout builder.

GameUI holds all mutable session state (current room, input buffer,
event history) and owns the Rich layout that is redrawn every frame.

Layout structure::

    +-----------+---------------------+----------+
    |   Chat    |   Current Events    |   Map    |
    |           |                     |----------|
    | --------- |                     |  Stats   |
    |  Event    |---------------------|----------|
    |  history  |  Command Input      | Inventory|
    +-----------+---------------------+----------+
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.layout import Layout

from Objects.Characters.character import NonPlayerCharacter, PlayerCharacter
from Objects.Rooms.room import Room
from UI.commands import CommandDispatcher
from UI.map_renderer import MapRenderer
from UI.panels import (
	CommandInputPanel,
	CoreStatsPanel,
	CurrentEventsPanel,
	EventHistoryPanel,
	RoomCharactersPanel,
	RoomChat,
	RoomInfoPanel,
	StatsPanel,
)
from UI.viewsClass import View

from logic.actions import COMMAND_REGISTRY

if TYPE_CHECKING:
	from server.world_manager import WorldManager


class GameUI(View):
	"""Central state object shared between the render loop and input thread.

	Attributes:
		MAX_HISTORY: Maximum number of event-log entries kept in memory.
		current_room: The room the player is currently in.
		event_history: Chronological list of Rich-markup log messages.
		player: The PlayerCharacter for this session.
		character_id: DB id of the character (used for saves and world tracking).
	"""

	MAX_HISTORY = 60
	MAX_CURRENT_EVENTS_HISTORY = 100

	def __init__(
		self,
		world_manager: WorldManager,
		player: PlayerCharacter,
		character_id: int,
		account_id: int,
	) -> None:
		super().__init__()
		self.world_manager = world_manager
		self.player = player
		self.character_id = character_id
		self.account_id = account_id
		self.current_room: Room = world_manager.start_room
		self.visited_rooms: set[Room] = {self.current_room}
		self.event_history: list[str] = [
			"[dim]Welcome to the MUD! Type [bold]help[/bold] for commands.[/dim]",
		]
		self.room_chat: list[str] = []
		self.current_events: list[str] = []
		self.current_events_history: list[str] = []
		self.current_events_offset: int = 0
		self.last_talked_npc: NonPlayerCharacter | None = None
		self._dispatcher = CommandDispatcher()

		# Register with the shared world
		world_manager.join(
			character_id,
			player,
			self.current_room,
			self._receive_event,
			self._receive_chat,
		)

		# Show the starting room description immediately
		self._dispatcher.dispatch(self, "look")

	def _receive_event(self, message: str) -> None:
		"""Callback invoked by WorldManager to push events into this session."""
		self.event_history.append(message)

	def _receive_chat(self, message: str) -> None:
		"""Callback invoked by WorldManager to push chat messages into this session."""
		self.room_chat.append(message)

	def _handle_input(self, text: str) -> None:
		"""Dispatch command through the command dispatcher."""
		self._dispatcher.dispatch(self, text)

	# -- current events history --------------------------------------------

	def append_current_events(self, messages: list[str]) -> None:
		"""Append messages to current_events and the persistent history buffer."""
		if self.current_events:
			self.current_events.append("")
		self.current_events.extend(messages)
		self.current_events_history.extend(messages)
		# Trim history to the most recent entries
		if len(self.current_events_history) > self.MAX_CURRENT_EVENTS_HISTORY:
			self.current_events_history = self.current_events_history[-self.MAX_CURRENT_EVENTS_HISTORY :]
		# Reset scroll to show the latest events
		self.current_events_offset = 0

	def scroll_events_up(self) -> None:
		"""Scroll current events history back by one line."""
		max_offset = max(0, len(self.current_events_history) - 1)
		self.current_events_offset = min(self.current_events_offset + 1, max_offset)

	def scroll_events_down(self) -> None:
		"""Scroll current events history forward by one line."""
		self.current_events_offset = max(0, self.current_events_offset - 1)

	# -- tab completion (delegates to base View / run_completion) ----------

	def _get_tab_candidates(self, partial: str) -> list[str]:
		"""Return completion candidates for commands and their arguments.

		When completing a command (first token), returns command names.
		When completing an argument, returns target names prefixed with
		the verb so that ``run_completion`` can set the full buffer.
		"""
		buffer = self.input_buffer
		parts = buffer.split(None, 1)
		completing_command = len(parts) == 0 or (len(parts) == 1 and not buffer.endswith(" "))

		if completing_command:
			p = partial.lower()
			return sorted({v for v in COMMAND_REGISTRY if v.startswith(p)})

		# Completing an argument
		verb = parts[0].lower()
		arg_partial = parts[1].lower() if len(parts) > 1 else ""

		target_type = COMMAND_REGISTRY.get(verb)
		if target_type is None:
			return []

		collectors = {
			"rooms": self._get_room_names,
			"items": self._get_item_names,
			"characters": self._get_character_names,
			"look_targets": self._get_look_targets,
			"all": self._get_all_targets,
		}
		collector = collectors.get(target_type, self._get_all_targets)
		all_names = collector()

		matches = sorted(
			[name for name in all_names if name.lower().startswith(arg_partial)],
			key=str.lower,
		)
		# Include the verb so run_completion sets the full buffer
		return [f"{verb} {name}" for name in matches]

	def _get_room_names(self) -> list[str]:
		return [r.name for r in self.current_room.connected_rooms.values()]

	def _get_item_names(self) -> list[str]:
		return [item.name for item in self.current_room.present_items]

	def _get_character_names(self) -> list[str]:
		names = [char.name for char in self.current_room.present_characters]
		for p in self.current_room.present_players:
			if p is not self.player:
				names.append(p.name)
		return names

	def _get_look_targets(self) -> list[str]:
		return self._get_item_names() + self._get_room_names()

	def _get_all_targets(self) -> list[str]:
		return self._get_item_names() + self._get_character_names() + self._get_room_names()

	# -- layout ------------------------------------------------------------

	def _build_layout(self) -> Layout:
		"""Construct the full Rich Layout for one frame."""
		layout = Layout()
		layout.split_row(
			Layout(name="left", ratio=1),
			Layout(name="middle", ratio=3),
			Layout(name="right", ratio=1),
		)

		layout["left"].split_column(
			Layout(name="chat", ratio=1),
			Layout(name="events", ratio=1),
		)
		layout["middle"].split_column(
			Layout(name="room_info", size=10),
			Layout(name="current_events", ratio=1),
			Layout(name="Core-stats", size=3),  ## hp and secondary resource bar (mana/stamina)
			Layout(name="writing", size=3),
		)
		layout["right"].split_column(
			Layout(name="map", ratio=1),
			Layout(name="stats", ratio=1),
			Layout(name="room_characters", ratio=1),
		)

		layout["chat"].update(RoomChat(self.room_chat, visible_count=5).build())
		layout["events"].update(EventHistoryPanel(self.event_history).build())
		layout["room_info"].update(RoomInfoPanel(self.current_room).build())
		layout["current_events"].update(
			CurrentEventsPanel(self.current_events_history, offset=self.current_events_offset).build()
		)
		layout["Core-stats"].update(CoreStatsPanel(self.player).build())
		layout["writing"].update(CommandInputPanel(self.input_buffer).build())
		layout["map"].update(MapRenderer(self.current_room, self.visited_rooms).build())
		in_combat = self.world_manager.combat_manager.is_in_combat(self.character_id)
		layout["stats"].update(StatsPanel(self.player, in_combat=in_combat).build())
		layout["room_characters"].update(RoomCharactersPanel(self.current_room).build())

		return layout
