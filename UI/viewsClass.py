"""Base View class for all UI screens.

Every screen in the game (character creation, in-game, menus, etc.)
inherits from View.  The base class provides:

- A view transition system via ``transition_to()``.
- Template methods ``_handle_input()`` and ``_build_layout()``
  that subclasses must implement.
- Automatic delegation to the *next_view* after a transition.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class View(ABC):
	"""Abstract base class for all UI views."""

	def __init__(self) -> None:
		self.running: bool = True
		self.input_buffer: str = ""
		self.next_view: View | None = None

	# -- transitions -------------------------------------------------------

	def transition_to(self, view_class, *args, **kwargs) -> None:
		"""Create a new view instance and delegate all future calls to it."""
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
			self.next_view.input_buffer = self.input_buffer
			self.running = self.next_view.running
			return self.next_view.build_layout()
		return self._build_layout()

	# -- template methods (subclasses must override) -----------------------

	@abstractmethod
	def _handle_input(self, text: str) -> None:
		"""Process submitted text. Subclasses implement game-specific logic."""

	@abstractmethod
	def _build_layout(self):
		"""Return a Rich Layout for this view. Rebuilt every frame."""
