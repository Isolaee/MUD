"""Action parsing and game-logic execution.

This module implements the two-phase command pipeline:

1. **Parse** — ``parse()`` converts raw user text into a typed
   ``(Action, inputs)`` tuple, resolving names to game objects.
2. **Execute** — ``execute()`` dispatches the action to the correct
   handler and returns an ``ActionResult`` with messages, optional
   room transition, and quit flag.

Adding a new command requires:
- A new ``Action`` enum member.
- A ``_resolve_*`` helper (if the command takes arguments).
- A ``_exec_*`` handler registered in ``execute()``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto

from Objects.room import Room


class Action(Enum):
	"""Every verb the player can type."""

	LOOK = auto()
	MOVE = auto()
	INVENTORY = auto()
	ATTACK = auto()
	Inspect = auto()
	PICK_UP = auto()
	DROP = auto()
	TALK_TO = auto()
	WHISPER = auto()
	HELP = auto()
	QUIT = auto()


@dataclass
class ActionResult:
	"""Value object returned by every execution handler.

	Attributes:
		messages: Rich-markup strings to append to the event log.
		new_room: If set, the player moves to this room.
		quit: If True, the game loop exits.
	"""

	messages: list[str] = field(default_factory=list)
	new_room: Room | None = None
	quit: bool = False


def parse(raw: str, current_room: Room) -> tuple[Action, list]:
	"""Parse raw user input into an Action and its resolved inputs.

	The first whitespace-delimited token is treated as the verb;
	everything after it is the argument.  If input is empty, defaults
	to LOOK at the current room.  Unrecognised verbs are treated as
	shorthand MOVE (i.e. typing a room name moves there).

	Returns:
		(Action, inputs) where *inputs* are resolved game objects
		or raw strings if resolution failed.
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

	# Bare word — try the full input as a room name (shorthand move)
	full = raw.strip().lower()
	target = _resolve_move_target(full, current_room)
	return Action.MOVE, [target]


def execute(action: Action, inputs: list, current_room: Room) -> ActionResult:
	"""Dispatch *action* to the matching handler and return the result."""
	handlers = {
		Action.LOOK: _exec_look,
		Action.MOVE: _exec_move,
		Action.INVENTORY: _exec_inventory,
		Action.HELP: _exec_help,
		Action.QUIT: _exec_quit,
	}
	return handlers[action](inputs, current_room)


# ---------------------------------------------------------------------------
# Resolution helpers — turn raw strings into game objects
# ---------------------------------------------------------------------------


def _resolve_look_target(arg: str, current_room: Room):
	"""Resolve look target: empty -> room, otherwise search items then rooms."""
	if not arg:
		return current_room

	# Search items in the room first
	for item in current_room.present_items:
		if item.name.lower() == arg:
			return item

	# Then search connected rooms
	for room in current_room.connected_rooms.values():
		if room.name.lower() == arg:
			return room

	return arg  # unresolved — will produce an error message


def _resolve_move_target(arg: str, current_room: Room):
	"""Resolve a movement target by matching against connected room names."""
	for room in current_room.connected_rooms.values():
		if room.name.lower() == arg:
			return room

	return arg  # unresolved


# ---------------------------------------------------------------------------
# Execution handlers — each returns an ActionResult
# ---------------------------------------------------------------------------


def _exec_look(inputs: list, current_room: Room) -> ActionResult:
	"""Display the description of a room, item, or other game object."""
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
		# Target string was never resolved to a game object
		result.messages.append(f"[red]You don't see '{target}' here.[/red]")

	return result


def _exec_move(inputs: list, current_room: Room) -> ActionResult:
	"""Move the player to a connected room, then auto-look."""
	result = ActionResult()

	if not inputs:
		result.messages.append("[red]Move where?[/red]")
		return result

	target = inputs[0]

	if isinstance(target, Room):
		result.messages.append(f"[dim]You move to {target.name}.[/dim]")
		result.new_room = target
		# Auto-look at the new room so the player sees its description
		look_result = _exec_look([target], target)
		result.messages.extend(look_result.messages)
	else:
		result.messages.append(f"[red]Unknown command:[/red] {target}. Type [bold]help[/bold] for commands.")

	return result


def _exec_inventory(inputs: list, current_room: Room) -> ActionResult:
	"""List items present in the current room."""
	result = ActionResult()
	items = current_room.present_items
	if not items:
		result.messages.append("[dim]Nothing here.[/dim]")
	else:
		for item in items:
			result.messages.append(f"  [white]- {item.name}[/white]")
	return result


def _exec_help(inputs: list, current_room: Room) -> ActionResult:
	"""Show available commands and current room exits."""
	result = ActionResult()
	connections = current_room.connected_rooms
	exits = ", ".join(r.name for r in connections.values())
	commands = ", ".join(a.name.lower().replace("_", " ") for a in Action)
	result.messages.append(f"[bold]Commands:[/bold] {commands}")
	if exits:
		result.messages.append(f"[bold]Current exits:[/bold] {exits}")
	return result


def _exec_quit(inputs: list, current_room: Room) -> ActionResult:
	"""Signal the game loop to exit."""
	return ActionResult(quit=True)
