"""Command dispatch — bridges user input to game logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from logic.actions import execute, parse

if TYPE_CHECKING:
	from UI.game_ui import GameUI


def dispatch(ui: GameUI, raw: str) -> None:
	cmd = raw.strip()
	if not cmd:
		return

	action, inputs = parse(cmd, ui.current_room)
	result = execute(action, inputs, ui.current_room)

	ui.event_history.extend(result.messages)

	if result.new_room is not None:
		ui.current_room = result.new_room

	if result.quit:
		ui.running = False

	_trim_history(ui)


def _trim_history(ui: GameUI) -> None:
	if len(ui.event_history) > ui.MAX_HISTORY:
		cutoff = -ui.MAX_HISTORY
		ui.event_history = ui.event_history[cutoff:]
