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
	from Objects.Characters.character import PlayerCharacter
	from Objects.Items.item import Item
	from Objects.Rooms.room import Room


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
	"""Character stats panel wired to a PlayerCharacter."""

	def __init__(self, player: PlayerCharacter | None = None, in_combat: bool = False) -> None:
		self._player = player
		self._in_combat = in_combat

	def build(self) -> Panel:
		table = Table(show_header=False, box=None, padding=(0, 1))
		table.add_column("stats", style="bold")
		table.add_column("value", justify="right")
		if self._player is not None:
			p = self._player
			table.add_row("HP", f"[red]{p.hp}[/red]")
			table.add_row("STM", f"[blue]{p.stamina}[/blue]")
			table.add_row("ATK", str(p.base_attack))
			table.add_row("Class", p.character_class.name.capitalize())
			table.add_row("Race", p.race.name.capitalize())
			if self._in_combat:
				table.add_row("", "[bold red]IN COMBAT[/bold red]")
			elif p.is_knocked_out:
				table.add_row("", "[bold red]KNOCKED OUT[/bold red]")
		else:
			table.add_row("[dim]No character[/dim]", "")
		return Panel(
			table,
			title="[bold]Character Stats[/bold]",
			border_style="red",
			box=box.ROUNDED,
		)


class CoreStatsPanel:
	"""HP and stamina bars displayed between events and command input."""

	HEART = "♥"
	BAR_CHAR = "█"
	EMPTY_CHAR = "░"
	BAR_WIDTH = 20

	def __init__(self, player: PlayerCharacter) -> None:
		self._player = player

	def _hp_color(self, ratio: float) -> str:
		"""Return a color that shifts from green to red as HP drops."""
		if ratio > 0.6:
			return "green"
		if ratio > 0.3:
			return "yellow"
		return "red"

	def _build_bar(self, current: int, maximum: int, color: str) -> str:
		"""Build a progress bar string with Rich markup."""
		ratio = max(0.0, min(1.0, current / maximum)) if maximum > 0 else 0.0
		filled = round(ratio * self.BAR_WIDTH)
		empty = self.BAR_WIDTH - filled
		return f"[{color}]{self.BAR_CHAR * filled}[/{color}][dim]{self.EMPTY_CHAR * empty}[/dim]"

	def build(self) -> Panel:
		p = self._player
		hp_ratio = max(0.0, min(1.0, p.hp / p.max_hp)) if p.max_hp > 0 else 0.0
		hp_color = self._hp_color(hp_ratio)

		hp_bar = self._build_bar(p.hp, p.max_hp, hp_color)
		stm_bar = self._build_bar(p.stamina, p.max_stamina, "yellow")

		line = (
			f"[{hp_color}]{self.HEART}[/{hp_color}] {hp_bar} "
			f"[bold {hp_color}]{p.hp}/{p.max_hp}[/bold {hp_color}]"
			f"  ⚡ {stm_bar} "
			f"[bold yellow]{p.stamina}/{p.max_stamina}[/bold yellow]"
		)

		return Panel(
			Text.from_markup(line),
			border_style="bright_black",
			box=box.ROUNDED,
			height=3,
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
