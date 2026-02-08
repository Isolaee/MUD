"""Command dispatch — bridges user input to game logic.

This is the thin glue layer between the input handler (which collects
keystrokes) and the action system (which parses and executes commands).

Flow: user input -> dispatch() -> parse() -> execute() -> update UI state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from logic.actions import execute, parse

if TYPE_CHECKING:
	from UI.game_ui import GameUI


def dispatch(ui: GameUI, raw: str) -> None:
	"""Parse and execute a raw command string, then update UI state.

	Appends result messages to the event history, transitions the
	player to a new room if applicable, and stops the game loop
	on a quit action.
	"""
	cmd = raw.strip()
	if not cmd:
		return

	action, inputs = parse(cmd, ui.current_room)
	result = execute(action, inputs, ui.current_room)

	# Push messages into the scrollable event log
	ui.event_history.extend(result.messages)

	# Handle room transition
	if result.new_room is not None:
		ui.current_room = result.new_room

	# Handle quit
	if result.quit:
		ui.running = False

	_trim_history(ui)


def _trim_history(ui: GameUI) -> None:
	"""Keep event history within MAX_HISTORY entries by dropping the oldest."""
	if len(ui.event_history) > ui.MAX_HISTORY:
		cutoff = -ui.MAX_HISTORY
		ui.event_history = ui.event_history[cutoff:]
