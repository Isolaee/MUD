"""Rich panel builders for the TUI layout.

Each ``make_*`` function returns a Rich Panel that is slotted into
the Layout constructed by ``GameUI.build_layout()``.  Panels are
rebuilt every frame so they always reflect the latest game state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich import box
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
	from UI.game_ui import GameUI


def make_event_history(ui: GameUI) -> Panel:
	"""Build the scrollable event-history panel (left column).

	Shows the most recent 5 log messages from the event history.
	"""
	lines = "\n".join(ui.event_history[-5:])
	return Panel(
		Text.from_markup(lines),
		title="[bold]Event History[/bold]",
		border_style="bright_blue",
		box=box.ROUNDED,
	)


def make_current_events(ui: GameUI) -> Panel:
	"""Build the main view panel showing room name, description, exits, and items."""
	room = ui.current_room
	desc = room.description
	parts = [f"[bold]{room.name}[/bold]\n"]
	if desc:
		parts.append(desc.long or desc.short)
	# List exits as clickable-looking cyan names
	exits = ", ".join(f"[cyan]{r.name}[/cyan]" for r in room.connected_rooms.values())
	if exits:
		parts.append(f"\nExits: {exits}")
	# List items lying on the floor
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


def make_writing_interface(ui: GameUI) -> Panel:
	"""Build the command-input panel with a blinking-cursor character."""
	return Panel(
		Text.from_markup(f"> {ui.input_buffer}\u2588"),
		title="[bold]Command[/bold]",
		border_style="white",
		box=box.ROUNDED,
		height=3,
	)


def make_stats() -> Panel:
	"""Build the character stats panel (placeholder with hardcoded values).

	TODO: Wire up to a real PlayerCharacter once stats are implemented.
	"""
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


def make_inventory(ui: GameUI) -> Panel:
	"""Build the inventory panel listing items in the current room.

	Note: Currently shows room items, not character inventory.
	"""
	items = ui.current_room.present_items
	if items:
		lines = "\n".join(f"[white]{i + 1}.[/white] {item.name}" for i, item in enumerate(items))
	else:
		lines = "[dim]Nothing here.[/dim]"
	return Panel(
		Text.from_markup(lines),
		title="[bold]Inventory[/bold]",
		border_style="magenta",
		box=box.ROUNDED,
	)
