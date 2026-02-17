"""Base View class for all UI screens.

Every screen in the game (character creation, in-game, menus, etc.)
inherits from View.  The base class provides:

- A view transition system via ``transition_to()``.
- Generic tab completion via ``handle_tab()`` and ``_get_tab_candidates()``.
- Template methods ``_handle_input()`` and ``_build_layout()``
  that subclasses must implement.
- Automatic delegation to the *next_view* after a transition.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from UI.tab_completion import run_completion


class View(ABC):
	"""Abstract base class for all UI views."""

	def __init__(self) -> None:
		self.running: bool = True
		self.input_buffer: str = ""
		self.next_view: View | None = None
		self.completion_state = None

	# -- transitions -------------------------------------------------------

	def transition_to(self, view_class, *args, **kwargs) -> None:
		"""Create a new view instance and delegate all future calls to it."""
		self.input_buffer = ""
		self.next_view = view_class(*args, **kwargs)

	# -- public interface (called by InputHandler / Application) -----------

	def handle_input(self, text: str) -> None:
		"""Forward input to next_view if transitioned, else to subclass."""
		if self.next_view is not None:
			self.next_view.handle_input(text)
			return
		self._handle_input(text)

	def build_layout(self):
		"""Forward layout to next_view if transitioned, else to subclass."""
		if self.next_view is not None:
			self.running = self.next_view.running
			return self.next_view.build_layout()
		return self._build_layout()

	def handle_tab(self) -> None:
		"""Handle a Tab key press using the generic completion engine.

		Subclasses enable completion by overriding ``_get_tab_candidates()``.
		"""
		if self.next_view is not None:
			self.next_view.handle_tab()
			return
		run_completion(self)

	# -- template methods --------------------------------------------------

	@abstractmethod
	def _handle_input(self, text: str) -> None:
		"""Process submitted text. Subclasses implement game-specific logic."""

	@abstractmethod
	def _build_layout(self):
		"""Return a Rich Layout for this view. Rebuilt every frame."""

	def scroll_events_up(self) -> None:
		"""Scroll current events history back. Override in subclasses."""

	def scroll_events_down(self) -> None:
		"""Scroll current events history forward. Override in subclasses."""

	def _get_tab_candidates(self, partial: str) -> list[str]:
		"""Return completion candidates for the current input.

		Override in subclasses to enable tab completion.
		Default returns empty list (no completion).
		"""
		return []
