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

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.layout import Layout

from Objects.Characters.character import PlayerCharacter
from Objects.Rooms.room import Room
from UI.commands import CommandDispatcher
from UI.map_renderer import MapRenderer
from UI.panels import (
	CommandInputPanel,
	CurrentEventsPanel,
	EventHistoryPanel,
	InventoryPanel,
	StatsPanel,
)
from UI.tab_completion import CompletionState, common_prefix
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

	_TWO_WORD_VERBS = {"talk to": "talk_to"}

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
		self._dispatcher = CommandDispatcher()

		# Register with the shared world
		world_manager.join(character_id, player, self.current_room, self._receive_event)

		# Show the starting room description immediately
		self._dispatcher.dispatch(self, "look")

	def _receive_event(self, message: str) -> None:
		"""Callback invoked by WorldManager to push events into this session."""
		self.event_history.append(message)

	def _handle_input(self, text: str) -> None:
		"""Dispatch command through the command dispatcher."""
		self._dispatcher.dispatch(self, text)

	# -- tab completion (command-aware) ------------------------------------

	def handle_tab(self) -> None:
		"""Handle tab completion for game commands and arguments."""
		buffer = self.input_buffer
		state = self.completion_state

		# Reset state if buffer changed since last tab
		if state is not None and state.original_buffer != buffer:
			state = None
			self.completion_state = None

		# Determine context (command vs argument)
		parts = buffer.split(None, 1)
		completing_command = len(parts) == 0 or (len(parts) == 1 and not buffer.endswith(" "))

		verb = ""
		partial = ""
		verb_prefix = ""

		if completing_command:
			partial = parts[0] if parts else ""
			candidates = self._get_command_candidates(partial)
		else:
			verb = parts[0]
			partial = parts[1] if len(parts) > 1 else ""
			verb_prefix = verb + " "

			# Check for two-word verb: "talk to <arg>"
			if len(parts) > 1:
				for tw, registry_key in self._TWO_WORD_VERBS.items():
					prefix = tw[len(verb) :]
					if parts[1].lower().startswith(prefix.lstrip()):
						rest = parts[1][len(prefix.lstrip()) :].lstrip()
						partial = rest
						verb_prefix = tw + " "
						verb = registry_key
						break

			candidates = self._get_argument_candidates(verb, partial)

		if not candidates:
			return

		# First tab press
		if state is None:
			if len(candidates) == 1:
				self.input_buffer = verb_prefix + candidates[0]
				self.completion_state = None
				return

			prefix = common_prefix(candidates)
			state = CompletionState(
				candidates=candidates,
				cycle_index=0,
				original_buffer=buffer,
				tab_count=1,
			)

			if prefix and prefix.lower() != partial.lower():
				self.input_buffer = verb_prefix + prefix
				state.original_buffer = self.input_buffer

			self.completion_state = state
			return

		# Subsequent tab presses
		state.tab_count += 1

		if state.tab_count == 2:
			formatted = "  ".join(f"[cyan]{c}[/cyan]" for c in state.candidates)
			self.event_history.append(f"[dim]Completions:[/dim] {formatted}")
			state.original_buffer = self.input_buffer
		else:
			candidate = state.candidates[state.cycle_index]
			self.input_buffer = verb_prefix + candidate
			state.cycle_index = (state.cycle_index + 1) % len(state.candidates)
			state.original_buffer = self.input_buffer

	# -- candidate generators ----------------------------------------------

	@staticmethod
	def _get_command_candidates(partial: str) -> list[str]:
		p = partial.lower()
		return sorted({v for v in COMMAND_REGISTRY if v.startswith(p)})

	def _get_argument_candidates(self, verb: str, partial: str) -> list[str]:
		target_type = COMMAND_REGISTRY.get(verb.lower())
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

		p = partial.lower()
		return sorted(
			[name for name in all_names if name.lower().startswith(p)],
			key=str.lower,
		)

	def _get_room_names(self) -> list[str]:
		return [r.name for r in self.current_room.connected_rooms.values()]

	def _get_item_names(self) -> list[str]:
		return [item.name for item in self.current_room.present_items]

	def _get_character_names(self) -> list[str]:
		names = [char.name for char in self.current_room.present_characters]
		# Include other players in the room
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
		layout["map"].update(MapRenderer(self.current_room, self.visited_rooms).build())
		in_combat = self.world_manager.combat_manager.is_in_combat(self.character_id)
		layout["stats"].update(StatsPanel(self.player, in_combat=in_combat).build())
		layout["inventory"].update(InventoryPanel(self.player.inventory).build())

		return layout
