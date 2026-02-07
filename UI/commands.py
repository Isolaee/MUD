"""Command dispatch and handlers for the MUD game."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from UI.game_ui import GameUI


def dispatch(ui: GameUI, raw: str) -> None:
	cmd = raw.strip().lower()
	if not cmd:
		return

	if cmd == "look":
		_cmd_look(ui)
	elif cmd in ("inventory", "inv"):
		_cmd_inventory(ui)
	elif cmd == "help":
		_cmd_help(ui)
	elif cmd in ("quit", "exit"):
		ui.running = False
	else:
		_cmd_go(ui, cmd)

	_trim_history(ui)


def _cmd_go(ui: GameUI, target: str) -> None:
	target_lower = target.lower()
	connections = ui.current_room.connected_rooms
	for direction, room in connections.items():
		if room.name.lower() == target_lower:
			ui.current_room = room
			ui.event_history.append(f"[dim]You move {direction.name.replace('_', ' ').lower()} to {room.name}.[/dim]")
			_cmd_look(ui)
			return
	ui.event_history.append(f"[red]Unknown command:[/red] {target}. Type [bold]help[/bold] for commands.")


def _cmd_look(ui: GameUI) -> None:
	desc = ui.current_room.description
	if desc and desc.long:
		ui.event_history.append(f"[dim]{desc.long}[/dim]")
	elif desc:
		ui.event_history.append(f"[dim]{desc.short}[/dim]")


def _cmd_inventory(ui: GameUI) -> None:
	items = ui.current_room.present_items
	if not items:
		ui.event_history.append("[dim]Nothing here.[/dim]")
		return
	for item in items:
		ui.event_history.append(f"  [white]- {item.name}[/white]")


def _cmd_help(ui: GameUI) -> None:
	connections = ui.current_room.connected_rooms
	exits = ", ".join(f"{r.name} ({d.name.replace('_', ' ').lower()})" for d, r in connections.items())
	ui.event_history.append("[bold]Commands:[/bold] look, inventory (inv), help, quit")
	if exits:
		ui.event_history.append(f"[bold]Go to:[/bold] {exits}")


def _trim_history(ui: GameUI) -> None:
	if len(ui.event_history) > ui.MAX_HISTORY:
		cutoff = -ui.MAX_HISTORY
		ui.event_history = ui.event_history[cutoff:]
