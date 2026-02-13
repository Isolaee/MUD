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

from Objects.Characters.character import NonPlayerCharacter
from Objects.Rooms.room import Room

# Maps alias -> canonical command name.
# Canonical commands map to themselves implicitly.
COMMAND_ALIASES: dict[str, str] = {
	"mv": "move",
	"go": "move",
	"l": "look",
	"inv": "inventory",
	"i": "inventory",
	"exit": "quit",
	"q": "quit",
	"talk to": "talk_to",
	"examine": "inspect",
	"get": "pick_up",
	"grab": "pick_up",
	"take": "pick_up",
	"atk": "attack",
	"hit": "attack",
}

# Maps each known verb to the type of targets it expects.
# Used by tab_completion to generate context-aware candidates.
# None means the command takes no arguments.
_CANONICAL_COMMANDS: dict[str, str | None] = {
	"look": "look_targets",
	"move": "rooms",
	"inventory": None,
	"help": None,
	"quit": None,
	"attack": "characters",
	"inspect": "all",
	"pick_up": "items",
	"drop": "items",
	"talk_to": "characters",
	"whisper": "characters",
}

# Build full registry including aliases (each alias gets the same target type).
COMMAND_REGISTRY: dict[str, str | None] = {
	**_CANONICAL_COMMANDS,
	**{alias: _CANONICAL_COMMANDS[canon] for alias, canon in COMMAND_ALIASES.items() if canon in _CANONICAL_COMMANDS},
}


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

	# Resolve aliases to canonical command names
	verb = COMMAND_ALIASES.get(verb, verb)

	# Two-word alias: "talk to <target>"
	if verb == "talk" and arg.startswith("to "):
		verb = "talk_to"
		arg = arg[3:]
	elif verb == "talk" and arg == "to":
		verb = "talk_to"
		arg = ""

	if verb == "look":
		return Action.LOOK, [_resolve_look_target(arg, current_room)]

	if verb == "inventory":
		return Action.INVENTORY, []

	if verb == "help":
		return Action.HELP, []

	if verb == "quit":
		return Action.QUIT, []

	if verb == "talk_to":
		target = _resolve_character_target(arg, current_room)
		return Action.TALK_TO, [target]

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
		Action.TALK_TO: _exec_talk_to,
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


def _resolve_character_target(arg: str, current_room: Room):
	"""Resolve a character target by matching against characters in the room."""
	if not arg:
		return arg
	for char in current_room.present_characters:
		if char.name.lower() == arg:
			return char
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


def _exec_talk_to(inputs: list, current_room: Room) -> ActionResult:
	"""Talk to an NPC in the current room."""
	result = ActionResult()

	if not inputs or not inputs[0]:
		result.messages.append("[red]Talk to whom?[/red]")
		return result

	target = inputs[0]

	if isinstance(target, NonPlayerCharacter):
		result.messages.append(f"[dim]You talk to {target.name}.[/dim]")
		if target.quest is not None:
			quest = target.quest
			desc = quest.description
			if desc and desc.long:
				result.messages.append(f"[dim]{desc.long}[/dim]")
			elif desc and desc.short:
				result.messages.append(f"[dim]{desc.short}[/dim]")
			result.messages.append(f"[yellow]Quest available: {quest.name}[/yellow]")
		else:
			result.messages.append(f"[dim]{target.name} has nothing to say.[/dim]")
	elif isinstance(target, str):
		result.messages.append(f"[red]You don't see '{target}' here.[/red]")
	else:
		result.messages.append("[red]You can't talk to that.[/red]")

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
