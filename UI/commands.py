"""Command dispatch — bridges user input to game logic.

This is the thin glue layer between the input handler (which collects
keystrokes) and the action system (which parses and executes commands).

Flow: user input -> CommandDispatcher.dispatch() -> parse() -> execute() -> update UI state.

During combat, input is routed to CombatManager instead of the normal pipeline.
Party commands (invite, accept, decline, leave_party, party) are routed to PartyManager.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from Objects.Characters.character import Character, NonPlayerCharacter
from logic.actions import Action, execute, parse
from Quests.quest import QuestStatus
from UI.panels import CHAT_CHAR, CHAT_CHAT_CHAR, CHAT_CHAT_TEXT, CHAT_TEXT

if TYPE_CHECKING:
	from UI.in_game_ui.gameUI import GameUI


class CommandDispatcher:
	"""Parses and executes commands, updating the GameUI state."""

	def dispatch(self, ui: GameUI, raw: str) -> None:
		"""Parse and execute a raw command string, then update UI state.

		Appends result messages to the event history, transitions the
		player to a new room if applicable, and stops the game loop
		on a quit action.
		"""
		cmd = raw.strip()
		if not cmd:
			return

		world = getattr(ui, "world_manager", None)
		char_id = getattr(ui, "character_id", None)

		# If player is in combat, route input to combat system
		if world and char_id and world.combat_manager.is_in_combat(char_id):
			# Allow quit even during combat
			if cmd.lower() in ("quit", "exit", "q"):
				ui.running = False
				return
			messages = world.combat_manager.handle_combat_input(char_id, cmd, world)
			ui.event_history.extend(messages)
			self._trim_history(ui)
			return

		# If player is knocked out, block most actions
		if ui.player.is_knocked_out:
			if cmd.lower() in ("quit", "exit", "q"):
				ui.running = False
				return
			ui.event_history.append("[red]You are knocked out and cannot act.[/red]")
			self._trim_history(ui)
			return

		action, inputs = parse(cmd, ui.current_room)
		result = execute(action, inputs, ui.current_room)

		# Handle chat — broadcast to room chat panel
		if action == Action.CHAT and world and char_id:
			message = inputs[0] if inputs else ""
			if not message:
				ui.event_history.append("[red]Chat what?[/red]")
				self._trim_history(ui)
				return
			name = ui.player.name
			ui.room_chat.append(f"[{CHAT_CHAR}]{name}:[/{CHAT_CHAR}] [{CHAT_TEXT}]{message}[/{CHAT_TEXT}]")
			world.broadcast_chat_to_room(
				ui.current_room,
				f"[{CHAT_CHAT_CHAR}]{name}:[/{CHAT_CHAT_CHAR}] [{CHAT_CHAT_TEXT}]{message}[/{CHAT_CHAT_TEXT}]",
				exclude=char_id,
			)
			return

		# Handle accept — quest accept takes priority, falls through to party
		if action == Action.ACCEPT:
			quest_messages = self._try_accept_quest(inputs, ui)
			if quest_messages is not None:
				if ui.current_events:
					ui.current_events.append("")
				ui.current_events.extend(quest_messages)
				self._trim_history(ui)
				return
			# No quest context — fall through to party accept

		# Handle party commands via PartyManager
		if world and char_id and action in _PARTY_ACTIONS:
			messages = self._handle_party_action(action, inputs, ui, world, char_id)
			ui.event_history.extend(messages)
			self._trim_history(ui)
			return

		# Handle attack — start combat via CombatManager
		if action == Action.ATTACK and world and char_id:
			target = inputs[0] if inputs else None
			if isinstance(target, Character):
				messages = world.combat_manager.start_combat(char_id, target, ui.current_room, world)
				ui.event_history.extend(messages)
				self._trim_history(ui)
				return
			# If target wasn't resolved, fall through to show error from result

		# NPC dialog shows in the Current Events panel, not event history
		if action == Action.TALK_TO:
			target = inputs[0] if inputs else None
			ui.last_talked_npc = target if isinstance(target, NonPlayerCharacter) else None
			if ui.current_events:
				ui.current_events.append("")
			ui.current_events.extend(result.messages)
		else:
			ui.event_history.extend(result.messages)

		if result.new_room is not None:
			ui.current_events = []
			ui.last_talked_npc = None
			if world is not None and char_id is not None:
				moved = world.move_player(char_id, result.new_room)
				if not moved:
					# Movement was blocked (e.g. in combat) — don't update room
					self._trim_history(ui)
					return
			ui.current_room = result.new_room
			ui.visited_rooms.add(result.new_room)

			# Room visit triggers
			if not ui.player.has_visited(result.new_room):
				if result.new_room.first_time_visited_text:
					ui.event_history.append(result.new_room.first_time_visited_text)
				ui.player.visit_room(result.new_room)
			if result.new_room.on_enter_text:
				ui.event_history.append(result.new_room.on_enter_text)
			if result.new_room.on_enter_action:
				ui.event_history.extend(result.new_room.on_enter_action(ui.player, result.new_room))

		if result.quit:
			ui.running = False

		self._trim_history(ui)

	@staticmethod
	def _handle_party_action(action: Action, inputs: list, ui: GameUI, world, char_id: int) -> list[str]:
		"""Route party commands to the PartyManager."""
		pm = world.party_manager

		if action == Action.INVITE:
			target = inputs[0] if inputs else None
			if not target or not isinstance(target, Character):
				name = inputs[0] if inputs else ""
				return [f"[red]You don't see '{name}' here.[/red]"] if name else ["[red]Invite whom?[/red]"]
			# Find target's character_id
			target_id = None
			for cid, session in world.sessions.items():
				if session.player is target:
					target_id = cid
					break
			if target_id is None:
				return [f"[red]{target.name} is not a player.[/red]"]
			return pm.invite(char_id, target_id, world)

		if action == Action.ACCEPT:
			return pm.accept(char_id, world)

		if action == Action.DECLINE:
			return pm.decline(char_id, world)

		if action == Action.LEAVE_PARTY:
			return pm.leave_party(char_id, world)

		if action == Action.PARTY:
			return pm.show_party(char_id, world)

		return []

	@staticmethod
	def _try_accept_quest(inputs: list, ui: GameUI) -> list[str] | None:
		"""Try to accept quest(s) from the last talked NPC.

		Returns a list of messages for the current events panel,
		or None if there's no quest context (so caller falls through
		to party accept).
		"""
		npc = ui.last_talked_npc
		if npc is None or npc.quest is None:
			return None

		quest = npc.quest
		if quest.status != QuestStatus.NOT_STARTED:
			return [f"[dim]You have already accepted '{quest.name}'.[/dim]"]

		# If a quest name was given, check it matches
		quest_name_filter = inputs[0] if inputs else None
		if quest_name_filter and quest_name_filter.lower() != quest.name.lower():
			return [f"[red]No quest called '{quest_name_filter}' is available here.[/red]"]

		# Check requirements before accepting
		can_accept, unmet = quest.can_accept(ui.player)
		if not can_accept:
			messages = [f"[red]You cannot accept '{quest.name}' yet.[/red]"]
			for desc in unmet:
				messages.append(f"  [yellow]- {desc}[/yellow]")
			return messages

		quest.start()
		ui.player.quests.append(quest)
		return [
			f"[green]Quest accepted: {quest.name}[/green]",
			f"[dim]{quest.objectives[0].description}[/dim]" if quest.objectives else "",
		]

	@staticmethod
	def _trim_history(ui: GameUI) -> None:
		"""Keep event history within MAX_HISTORY entries by dropping the oldest."""
		if len(ui.event_history) > ui.MAX_HISTORY:
			ui.event_history = ui.event_history[-ui.MAX_HISTORY :]


_PARTY_ACTIONS = {
	Action.INVITE,
	Action.ACCEPT,
	Action.DECLINE,
	Action.LEAVE_PARTY,
	Action.PARTY,
}
