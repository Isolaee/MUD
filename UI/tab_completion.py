"""Linux-style tab-completion for the command input.

Handles Tab key presses by completing commands and arguments based on
the current input buffer and game state.  Follows bash conventions:

- 1st Tab with single match: fill immediately.
- 1st Tab with multiple matches: fill longest common prefix.
- 2nd Tab: show candidates in event history.
- 3rd+ Tab: cycle through candidates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from logic.actions import COMMAND_REGISTRY

if TYPE_CHECKING:
	from Objects.room import Room
	from UI.game_ui import GameUI


@dataclass
class CompletionState:
	"""Tracks state between consecutive Tab presses."""

	candidates: list[str]
	cycle_index: int = 0
	original_buffer: str = ""
	tab_count: int = 1


# ---------------------------------------------------------------------------
# Candidate generators
# ---------------------------------------------------------------------------


def _get_room_names(room: Room) -> list[str]:
	return [r.name for r in room.connected_rooms.values()]


def _get_item_names(room: Room) -> list[str]:
	return [item.name for item in room.present_items]


def _get_character_names(room: Room) -> list[str]:
	return [char.name for char in room.present_characters]


def _get_look_targets(room: Room) -> list[str]:
	return _get_item_names(room) + _get_room_names(room)


def _get_all_targets(room: Room) -> list[str]:
	return _get_item_names(room) + _get_character_names(room) + _get_room_names(room)


_TARGET_COLLECTORS = {
	"rooms": _get_room_names,
	"items": _get_item_names,
	"characters": _get_character_names,
	"look_targets": _get_look_targets,
	"all": _get_all_targets,
}


def _get_command_candidates(partial: str) -> list[str]:
	"""Return command verbs that start with *partial* (case-insensitive)."""
	p = partial.lower()
	return sorted({v for v in COMMAND_REGISTRY if v.startswith(p)})


def _get_argument_candidates(verb: str, partial: str, room: Room) -> list[str]:
	"""Return context-aware argument candidates for *verb*."""
	target_type = COMMAND_REGISTRY.get(verb.lower())
	if target_type is None:
		return []

	collector = _TARGET_COLLECTORS.get(target_type, _get_all_targets)
	all_names = collector(room)

	p = partial.lower()
	return sorted(
		[name for name in all_names if name.lower().startswith(p)],
		key=str.lower,
	)


# ---------------------------------------------------------------------------
# Prefix / apply helpers
# ---------------------------------------------------------------------------


def _common_prefix(candidates: list[str]) -> str:
	"""Find the longest case-insensitive common prefix among *candidates*."""
	if not candidates:
		return ""
	if len(candidates) == 1:
		return candidates[0]

	# Work on lowercased versions for comparison, then take original-case chars
	ref = candidates[0]
	length = min(len(c) for c in candidates)
	end = 0
	for i in range(length):
		if len({c[i].lower() for c in candidates}) == 1:
			end = i + 1
		else:
			break
	# Return the prefix using the first candidate's casing
	return ref[:end]


def _apply_completion(ui: GameUI, verb_part: str, completed: str) -> None:
	"""Replace the relevant portion of ui.input_buffer with *completed*.

	*verb_part* is the command prefix (e.g. "move ") that stays intact;
	*completed* replaces whatever followed it.
	"""
	if verb_part:
		ui.input_buffer = verb_part + completed
	else:
		ui.input_buffer = completed


def _show_candidates(ui: GameUI, candidates: list[str]) -> None:
	"""Display completion candidates in the event history panel."""
	formatted = "  ".join(f"[cyan]{c}[/cyan]" for c in candidates)
	ui.event_history.append(f"[dim]Completions:[/dim] {formatted}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def complete(ui: GameUI) -> None:
	"""Handle a Tab key press — the only function called from input_handler."""
	buffer = ui.input_buffer
	state = ui.completion_state

	# If the buffer changed since last tab, reset state
	if state is not None and state.original_buffer != buffer:
		state = None
		ui.completion_state = None

	# --- Determine context (command vs argument) ---
	parts = buffer.split(None, 1)
	completing_command = len(parts) == 0 or (len(parts) == 1 and not buffer.endswith(" "))

	if completing_command:
		partial = parts[0] if parts else ""
		verb_prefix = ""
		candidates = _get_command_candidates(partial)
	else:
		verb = parts[0]
		partial = parts[1] if len(parts) > 1 else ""
		# Keep everything up to and including the space after the verb
		verb_prefix = verb + " "
		candidates = _get_argument_candidates(verb, partial, ui.current_room)

	if not candidates:
		return

	# --- First tab press (no active state) ---
	if state is None:
		if len(candidates) == 1:
			# Single match — fill immediately
			_apply_completion(ui, verb_prefix, candidates[0])
			ui.completion_state = None
			return

		# Multiple matches — fill common prefix
		prefix = _common_prefix(candidates)
		state = CompletionState(
			candidates=candidates,
			cycle_index=0,
			original_buffer=buffer,
			tab_count=1,
		)

		if prefix and prefix.lower() != partial.lower():
			_apply_completion(ui, verb_prefix, prefix)
			state.original_buffer = ui.input_buffer

		ui.completion_state = state
		return

	# --- Subsequent tab presses ---
	state.tab_count += 1

	if state.tab_count == 2:
		# Second tab — show candidates in event log
		_show_candidates(ui, state.candidates)
		state.original_buffer = ui.input_buffer
	else:
		# Third+ tab — cycle through candidates
		candidate = state.candidates[state.cycle_index]
		_apply_completion(ui, verb_prefix, candidate)
		state.cycle_index = (state.cycle_index + 1) % len(state.candidates)
		state.original_buffer = ui.input_buffer
