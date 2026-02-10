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
	from UI.in_game_ui.gameUI import GameUI


@dataclass
class CompletionState:
	"""Tracks state between consecutive Tab presses."""

	candidates: list[str]
	cycle_index: int = 0
	original_buffer: str = ""
	tab_count: int = 1


class TabCompleter:
	"""Bash-style tab completion for game commands and arguments."""

	_TWO_WORD_VERBS = {"talk to": "talk_to"}

	# -- candidate generators ---------------------------------------------

	@staticmethod
	def _get_room_names(room: Room) -> list[str]:
		return [r.name for r in room.connected_rooms.values()]

	@staticmethod
	def _get_item_names(room: Room) -> list[str]:
		return [item.name for item in room.present_items]

	@staticmethod
	def _get_character_names(room: Room) -> list[str]:
		return [char.name for char in room.present_characters]

	def _get_look_targets(self, room: Room) -> list[str]:
		return self._get_item_names(room) + self._get_room_names(room)

	def _get_all_targets(self, room: Room) -> list[str]:
		return self._get_item_names(room) + self._get_character_names(room) + self._get_room_names(room)

	def _get_command_candidates(self, partial: str) -> list[str]:
		"""Return command verbs that start with *partial* (case-insensitive)."""
		p = partial.lower()
		return sorted({v for v in COMMAND_REGISTRY if v.startswith(p)})

	def _get_argument_candidates(self, verb: str, partial: str, room: Room) -> list[str]:
		"""Return context-aware argument candidates for *verb*."""
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
		all_names = collector(room)

		p = partial.lower()
		return sorted(
			[name for name in all_names if name.lower().startswith(p)],
			key=str.lower,
		)

	# -- helpers -----------------------------------------------------------

	@staticmethod
	def _common_prefix(candidates: list[str]) -> str:
		"""Find the longest case-insensitive common prefix among *candidates*."""
		if not candidates:
			return ""
		if len(candidates) == 1:
			return candidates[0]

		ref = candidates[0]
		length = min(len(c) for c in candidates)
		end = 0
		for i in range(length):
			if len({c[i].lower() for c in candidates}) == 1:
				end = i + 1
			else:
				break
		return ref[:end]

	@staticmethod
	def _apply_completion(ui: GameUI, verb_part: str, completed: str) -> None:
		"""Replace the relevant portion of ui.input_buffer with *completed*."""
		if verb_part:
			ui.input_buffer = verb_part + completed
		else:
			ui.input_buffer = completed

	@staticmethod
	def _show_candidates(ui: GameUI, candidates: list[str]) -> None:
		"""Display completion candidates in the event history panel."""
		formatted = "  ".join(f"[cyan]{c}[/cyan]" for c in candidates)
		ui.event_history.append(f"[dim]Completions:[/dim] {formatted}")

	# -- main entry point --------------------------------------------------

	def complete(self, ui: GameUI) -> None:
		"""Handle a Tab key press."""
		buffer = ui.input_buffer
		state = ui.completion_state

		# If the buffer changed since last tab, reset state
		if state is not None and state.original_buffer != buffer:
			state = None
			ui.completion_state = None

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

			candidates = self._get_argument_candidates(verb, partial, ui.current_room)

		if not candidates:
			return

		# First tab press (no active state)
		if state is None:
			if len(candidates) == 1:
				self._apply_completion(ui, verb_prefix, candidates[0])
				ui.completion_state = None
				return

			prefix = self._common_prefix(candidates)
			state = CompletionState(
				candidates=candidates,
				cycle_index=0,
				original_buffer=buffer,
				tab_count=1,
			)

			if prefix and prefix.lower() != partial.lower():
				self._apply_completion(ui, verb_prefix, prefix)
				state.original_buffer = ui.input_buffer

			ui.completion_state = state
			return

		# Subsequent tab presses
		state.tab_count += 1

		if state.tab_count == 2:
			self._show_candidates(ui, state.candidates)
			state.original_buffer = ui.input_buffer
		else:
			candidate = state.candidates[state.cycle_index]
			self._apply_completion(ui, verb_prefix, candidate)
			state.cycle_index = (state.cycle_index + 1) % len(state.candidates)
			state.original_buffer = ui.input_buffer
