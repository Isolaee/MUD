"""Rich panel classes for the TUI layout.

Each panel class takes the data it needs in its constructor and
exposes a ``build()`` method that returns a Rich Panel.  Panels
are rebuilt every frame so they always reflect the latest state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
	from Objects.item import Item
	from Objects.room import Room


class EventHistoryPanel:
	"""Scrollable event history (left column)."""

	def __init__(self, event_history: list[str], visible_count: int = 5) -> None:
		self._history = event_history
		self._visible = visible_count

	def build(self) -> Panel:
		lines = "\n".join(self._history[-self._visible :])
		return Panel(
			Text.from_markup(lines),
			title="[bold]Event History[/bold]",
			border_style="bright_blue",
			box=box.ROUNDED,
		)


class CurrentEventsPanel:
	"""Main view showing room name, description, exits, and items."""

	def __init__(self, room: Room) -> None:
		self._room = room

	def build(self) -> Panel:
		room = self._room
		desc = room.description
		parts = [f"[bold]{room.name}[/bold]\n"]
		if desc:
			parts.append(desc.long or desc.short)
		exits = ", ".join(f"[cyan]{r.name}[/cyan]" for r in room.connected_rooms.values())
		if exits:
			parts.append(f"\nExits: {exits}")
		items = room.present_items
		if items:
			parts.append("\n[yellow]Items here:[/yellow]")
			for item in items:
				parts.append(f"  - {item.name}")
		return Panel(
			Text.from_markup("\n".join(parts)),
			title="[bold]Current Events[/bold]",
			border_style="green",
			box=box.ROUNDED,
		)


class CommandInputPanel:
	"""Command input line with blinking cursor."""

	def __init__(self, input_buffer: str) -> None:
		self._buffer = input_buffer

	def build(self) -> Panel:
		return Panel(
			Text.from_markup(f"> {self._buffer}\u2588"),
			title="[bold]Command[/bold]",
			border_style="white",
			box=box.ROUNDED,
			height=3,
		)


class StatsPanel:
	"""Character stats (placeholder with hardcoded values).

	TODO: Wire up to a real PlayerCharacter once stats are implemented.
	"""

	def build(self) -> Panel:
		table = Table(show_header=False, box=None, padding=(0, 1))
		table.add_column("stats", style="bold")
		table.add_column("value", justify="right")
		table.add_row("HP", "[red]45[/red] / 60")
		table.add_row("MP", "[blue]20[/blue] / 20")
		table.add_row("STR", "14")
		table.add_row("DEX", "12")
		table.add_row("INT", "10")
		table.add_row("Level", "[bold]3[/bold]")
		table.add_row("XP", "230 / 500")
		return Panel(
			table,
			title="[bold]Character Stats[/bold]",
			border_style="red",
			box=box.ROUNDED,
		)


class InventoryPanel:
	"""Inventory panel listing items.

	Note: Currently shows room items, not character inventory.
	"""

	def __init__(self, items: list[Item]) -> None:
		self._items = items

	def build(self) -> Panel:
		if self._items:
			lines = "\n".join(f"[white]{i + 1}.[/white] {item.name}" for i, item in enumerate(self._items))
		else:
			lines = "[dim]Nothing here.[/dim]"
		return Panel(
			Text.from_markup(lines),
			title="[bold]Inventory[/bold]",
			border_style="magenta",
			box=box.ROUNDED,
		)
