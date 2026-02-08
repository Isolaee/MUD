"""Action enum and game logic execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from Objects.room import Direction, Room


class Action(Enum):
	LOOK = auto()
	MOVE = auto()
	INVENTORY = auto()
	HELP = auto()
	QUIT = auto()


@dataclass
class ActionResult:
	messages: list[str] = field(default_factory=list)
	new_room: Room | None = None
	quit: bool = False


# Map direction name strings to Direction enum for movement shortcuts.
_DIRECTION_NAMES: dict[str, Direction] = {d.name.lower().replace("_", " "): d for d in Direction}


def parse(raw: str, current_room: Room) -> tuple[Action, list]:
	"""Parse raw user input into an Action and its resolved inputs.

	Returns (Action, inputs) where inputs are typed game objects.
	"""
	parts = raw.strip().lower().split(None, 1)
	if not parts:
		return Action.LOOK, [current_room]

	verb = parts[0]
	arg = parts[1] if len(parts) > 1 else ""

	if verb == "look":
		return Action.LOOK, [_resolve_look_target(arg, current_room)]

	if verb in ("inventory", "inv"):
		return Action.INVENTORY, []

	if verb == "help":
		return Action.HELP, []

	if verb in ("quit", "exit"):
		return Action.QUIT, []

	if verb == "move" and arg:
		target = _resolve_move_target(arg, current_room)
		return Action.MOVE, [target]

	# Bare word — try as direction name or room name
	full = raw.strip().lower()
	target = _resolve_move_target(full, current_room)
	return Action.MOVE, [target]


def execute(action: Action, inputs: list, current_room: Room) -> ActionResult:
	"""Execute an action with resolved inputs. Returns an ActionResult."""
	handlers = {
		Action.LOOK: _exec_look,
		Action.MOVE: _exec_move,
		Action.INVENTORY: _exec_inventory,
		Action.HELP: _exec_help,
		Action.QUIT: _exec_quit,
	}
	return handlers[action](inputs, current_room)


# ---------------------------------------------------------------------------
# Resolution helpers
# ---------------------------------------------------------------------------


def _resolve_look_target(arg: str, current_room: Room):
	"""Resolve look target: empty → room, otherwise search items then rooms."""
	if not arg:
		return current_room

	# Search items in the room
	for item in current_room.present_items:
		if item.name.lower() == arg:
			return item

	# Search connected rooms
	for room in current_room.connected_rooms.values():
		if room.name.lower() == arg:
			return room

	return arg  # unresolved — will produce an error message


def _resolve_move_target(arg: str, current_room: Room):
	"""Resolve a movement target by direction name or room name."""
	# Try direction name (e.g. "north", "south east")
	if arg in _DIRECTION_NAMES:
		direction = _DIRECTION_NAMES[arg]
		if direction in current_room.connected_rooms:
			return current_room.connected_rooms[direction]

	# Try room name
	for room in current_room.connected_rooms.values():
		if room.name.lower() == arg:
			return room

	return arg  # unresolved


# ---------------------------------------------------------------------------
# Execution handlers
# ---------------------------------------------------------------------------


def _exec_look(inputs: list, current_room: Room) -> ActionResult:
	target = inputs[0] if inputs else current_room
	result = ActionResult()

	if isinstance(target, Room):
		desc = target.description
		if desc and desc.long:
			result.messages.append(f"[dim]{desc.long}[/dim]")
		elif desc:
			result.messages.append(f"[dim]{desc.short}[/dim]")
	elif hasattr(target, "name"):
		# It's an item or other game object
		result.messages.append(f"[white]{target.name}[/white]")
		if hasattr(target, "description") and target.description:
			desc = target.description
			if hasattr(desc, "long") and desc.long:
				result.messages.append(f"[dim]{desc.long}[/dim]")
			elif hasattr(desc, "short"):
				result.messages.append(f"[dim]{desc.short}[/dim]")
	else:
		result.messages.append(f"[red]You don't see '{target}' here.[/red]")

	return result


def _exec_move(inputs: list, current_room: Room) -> ActionResult:
	result = ActionResult()

	if not inputs:
		result.messages.append("[red]Move where?[/red]")
		return result

	target = inputs[0]

	if isinstance(target, Room):
		# Find the direction for the message
		for direction, room in current_room.connected_rooms.items():
			if room is target:
				result.messages.append(
					f"[dim]You move {direction.name.replace('_', ' ').lower()} to {target.name}.[/dim]"
				)
				break
		result.new_room = target
		# Auto-look at new room
		look_result = _exec_look([target], target)
		result.messages.extend(look_result.messages)
	else:
		result.messages.append(f"[red]Unknown command:[/red] {target}. Type [bold]help[/bold] for commands.")

	return result


def _exec_inventory(inputs: list, current_room: Room) -> ActionResult:
	result = ActionResult()
	items = current_room.present_items
	if not items:
		result.messages.append("[dim]Nothing here.[/dim]")
	else:
		for item in items:
			result.messages.append(f"  [white]- {item.name}[/white]")
	return result


def _exec_help(inputs: list, current_room: Room) -> ActionResult:
	result = ActionResult()
	connections = current_room.connected_rooms
	exits = ", ".join(f"{r.name} ({d.name.replace('_', ' ').lower()})" for d, r in connections.items())
	result.messages.append("[bold]Commands:[/bold] look [target], move <direction/room>, inventory (inv), help, quit")
	if exits:
		result.messages.append(f"[bold]Go to:[/bold] {exits}")
	return result


def _exec_quit(inputs: list, current_room: Room) -> ActionResult:
	return ActionResult(quit=True)
