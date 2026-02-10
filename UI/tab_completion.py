"""Generic bash-style tab completion.

The completion engine lives in the base View class (via CompletionMixin).
Each view provides candidates by overriding ``_get_tab_candidates()``.

The engine handles:
- 1st Tab with single match: fill immediately.
- 1st Tab with multiple matches: fill longest common prefix.
- 2nd Tab: show candidates (if view has event_history).
- 3rd+ Tab: cycle through candidates.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CompletionState:
	"""Tracks state between consecutive Tab presses."""

	candidates: list[str]
	cycle_index: int = 0
	original_buffer: str = ""
	tab_count: int = 1


def common_prefix(candidates: list[str]) -> str:
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


def run_completion(view) -> None:
	"""Execute one Tab press against a view.

	Expects the view to have:
	- input_buffer: str
	- completion_state: CompletionState | None
	- _get_tab_candidates(partial: str) -> list[str]
	- (optional) event_history: list[str]  — for showing candidates
	"""
	buffer = view.input_buffer
	state = view.completion_state

	# Reset state if buffer changed since last tab
	if state is not None and state.original_buffer != buffer:
		state = None
		view.completion_state = None

	partial = buffer.strip().lower()
	candidates = view._get_tab_candidates(partial)

	if not candidates:
		return

	# First tab press (no active state)
	if state is None:
		if len(candidates) == 1:
			view.input_buffer = candidates[0]
			view.completion_state = None
			return

		prefix = common_prefix(candidates)
		state = CompletionState(
			candidates=candidates,
			cycle_index=0,
			original_buffer=buffer,
			tab_count=1,
		)

		if prefix and prefix.lower() != partial:
			view.input_buffer = prefix
			state.original_buffer = view.input_buffer

		view.completion_state = state
		return

	# Subsequent tab presses
	state.tab_count += 1

	if state.tab_count == 2:
		# Show candidates if view supports event history
		if hasattr(view, "event_history"):
			formatted = "  ".join(f"[cyan]{c}[/cyan]" for c in state.candidates)
			view.event_history.append(f"[dim]Completions:[/dim] {formatted}")
		state.original_buffer = view.input_buffer
	else:
		# Cycle through candidates
		candidate = state.candidates[state.cycle_index]
		view.input_buffer = candidate
		state.cycle_index = (state.cycle_index + 1) % len(state.candidates)
		state.original_buffer = view.input_buffer
