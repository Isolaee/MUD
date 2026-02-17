"""Action parsing and game-logic execution.

This module implements the two-phase command pipeline:

1. **Parse** — ``parse()`` converts raw user text into a typed
   ``(Action, inputs)`` tuple, resolving names to game objects.
2. **Execute** — ``execute()`` dispatches the action to the correct
   handler and returns an ``ActionResult`` with messages, optional
   room transition, and quit flag.

Adding a new command requires:
- A new ``Action`` enum member.
- An entry in ``_PARSE_TABLE`` (with a resolver if the command takes arguments).
- An entry in ``_EXEC_HANDLERS``.
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
	"tt": "talk-to",
	"whisper": "whisper",
	"examine": "inspect",
	"get": "pick-up",
	"grab": "pick-up",
	"take": "pick-up",
	"atk": "attack",
	"hit": "attack",
	"lp": "leave-party",
}

# Maps each known verb to the type of targets it expects for tab completion.
# None means the command takes no arguments.
# Implemented commands are listed here alongside stubs for future commands.
_CANONICAL_COMMANDS: dict[str, str | None] = {
	"look": "look_targets",
	"move": "rooms",
	"attack": "characters",
	"invite": "characters",
	"talk-to": "characters",
	"inspect": "all",
	"pick-up": "items",
	"drop": "items",
	"whisper": "characters",
	# Commands with no tab-completion targets
	"inventory": None,
	"help": None,
	"quit": None,
	"accept": None,
	"decline": None,
	"leave-party": None,
	"party": None,
	"chat": None,
	"defend": None,
	"flee": None,
	"login": None,
	"register": None,
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
	INSPECT = auto()
	PICK_UP = auto()
	DROP = auto()
	TALK_TO = auto()
	WHISPER = auto()
	INVITE = auto()
	ACCEPT = auto()
	DECLINE = auto()
	LEAVE_PARTY = auto()
	PARTY = auto()
	CHAT = auto()
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


def _resolve_character_target(arg: str, current_room: Room, include_players: bool = False):
	"""Resolve a character target by name in the current room.

	Searches NPCs first, then optionally players.
	"""
	if not arg:
		return arg
	for char in current_room.present_characters:
		if char.name.lower() == arg:
			return char
	if include_players:
		for player in current_room.present_players:
			if player.name.lower() == arg:
				return player
	return arg  # unresolved


# ---------------------------------------------------------------------------
# Parse table — maps canonical verb to (Action, resolver)
# ---------------------------------------------------------------------------

# Maps canonical verb -> (Action, resolver | "raw" | None).
# - None: no arguments expected.
# - "raw": pass the raw argument string as-is.
# - callable: resolver(arg, current_room) -> resolved target.
_PARSE_TABLE: dict[str, tuple[Action, object]] = {
	"look": (Action.LOOK, _resolve_look_target),
	"move": (Action.MOVE, _resolve_move_target),
	"inventory": (Action.INVENTORY, None),
	"help": (Action.HELP, None),
	"quit": (Action.QUIT, None),
	"attack": (Action.ATTACK, lambda arg, room: _resolve_character_target(arg, room, include_players=True)),
	"invite": (Action.INVITE, lambda arg, room: _resolve_character_target(arg, room, include_players=True)),
	"accept": (Action.ACCEPT, "raw"),
	"decline": (Action.DECLINE, None),
	"leave-party": (Action.LEAVE_PARTY, None),
	"party": (Action.PARTY, None),
	"talk-to": (Action.TALK_TO, _resolve_character_target),
	"chat": (Action.CHAT, "raw"),
}


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

	entry = _PARSE_TABLE.get(verb)
	if entry is not None:
		action, resolver = entry
		if resolver is None:
			return action, []
		if resolver == "raw":
			return action, [arg] if arg else []
		return action, [resolver(arg, current_room)]

	# Unrecognised verbs are treated as shorthand MOVE
	# (typing a room name moves there).
	full = raw.strip().lower()
	target = _resolve_move_target(full, current_room)
	return Action.MOVE, [target]


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
	"""List items on the ground in the current room.

	NOTE: A proper player inventory command would require passing the
	player object through the execute pipeline.
	"""
	result = ActionResult()
	items = current_room.present_items
	if not items:
		result.messages.append("[dim]Nothing here.[/dim]")
	else:
		result.messages.append("[bold]Items here:[/bold]")
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
		result.messages = target.interact()
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
	commands = ", ".join(a.name.lower().replace("_", "-") for a in Action)
	result.messages.append(f"[bold]Commands:[/bold] {commands}")
	if exits:
		result.messages.append(f"[bold]Current exits:[/bold] {exits}")
	return result


def _exec_attack(inputs: list, current_room: Room) -> ActionResult:
	"""Resolve attack target. Actual combat is started by CommandDispatcher."""
	result = ActionResult()
	if not inputs or not inputs[0]:
		result.messages.append("[red]Attack whom?[/red]")
		return result

	target = inputs[0]
	if isinstance(target, str):
		result.messages.append(f"[red]You don't see '{target}' here.[/red]")
	# If target is a Character, CommandDispatcher will handle starting combat
	return result


def _exec_noop(inputs: list, current_room: Room) -> ActionResult:
	"""Placeholder for commands handled entirely by CommandDispatcher."""
	return ActionResult()


def _exec_quit(inputs: list, current_room: Room) -> ActionResult:
	"""Signal the game loop to exit."""
	return ActionResult(quit=True)


# ---------------------------------------------------------------------------
# Execution dispatch table — built once at module level
# ---------------------------------------------------------------------------

_EXEC_HANDLERS: dict[Action, callable] = {
	Action.LOOK: _exec_look,
	Action.MOVE: _exec_move,
	Action.INVENTORY: _exec_inventory,
	Action.ATTACK: _exec_attack,
	Action.TALK_TO: _exec_talk_to,
	Action.HELP: _exec_help,
	Action.QUIT: _exec_quit,
	# Chat and party commands return empty results; handled by CommandDispatcher
	Action.CHAT: _exec_noop,
	Action.INVITE: _exec_noop,
	Action.ACCEPT: _exec_noop,
	Action.DECLINE: _exec_noop,
	Action.LEAVE_PARTY: _exec_noop,
	Action.PARTY: _exec_noop,
}


def execute(action: Action, inputs: list, current_room: Room) -> ActionResult:
	"""Dispatch *action* to the matching handler and return the result."""
	return _EXEC_HANDLERS[action](inputs, current_room)
