"""Party system for grouping players.

Parties allow up to 4 players to group together.  When one party member
initiates combat, all members in the same room join automatically.

Usage:
    invite [player]  — send a party invite
    accept           — accept a pending invite
    decline          — decline a pending invite
    leave party      — leave your current party
    party            — show current party members
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from server.world_manager import WorldManager

MAX_PARTY_SIZE = 4


class PartyManager:
	"""Manages party formation and membership."""

	def __init__(self) -> None:
		# leader_id -> list of all member character_ids (including leader)
		self.parties: dict[int, list[int]] = {}
		# invitee_id -> inviter_id
		self.invites: dict[int, int] = {}

	def _find_party_leader(self, character_id: int) -> int | None:
		"""Return the leader id of the party *character_id* belongs to."""
		for leader, members in self.parties.items():
			if character_id in members:
				return leader
		return None

	def get_party_members(self, character_id: int) -> list[int]:
		"""Return all member ids in *character_id*'s party, or just [character_id]."""
		leader = self._find_party_leader(character_id)
		if leader is None:
			return [character_id]
		return list(self.parties[leader])

	def get_party_members_in_room(self, character_id: int, room_uid: str, world: WorldManager) -> list[int]:
		"""Return party member ids that are in the same room."""
		members = self.get_party_members(character_id)
		result = []
		for mid in members:
			session = world.sessions.get(mid)
			if session and session.room.uid == room_uid:
				result.append(mid)
		return result

	def invite(self, inviter_id: int, invitee_id: int, world: WorldManager) -> list[str]:
		"""Send a party invite. Returns messages for the inviter."""
		inviter_session = world.sessions.get(inviter_id)
		invitee_session = world.sessions.get(invitee_id)
		if not inviter_session or not invitee_session:
			return ["[red]Player not found.[/red]"]

		# Check same room
		if inviter_session.room is not invitee_session.room:
			return ["[red]That player is not in this room.[/red]"]

		# Check if invitee already in a party
		if self._find_party_leader(invitee_id) is not None:
			return [f"[red]{invitee_session.player.name} is already in a party.[/red]"]

		# Check party size
		members = self.get_party_members(inviter_id)
		if len(members) >= MAX_PARTY_SIZE:
			return ["[red]Your party is full (max 4).[/red]"]

		# Check for pending invite
		if invitee_id in self.invites:
			return [f"[red]{invitee_session.player.name} already has a pending invite.[/red]"]

		self.invites[invitee_id] = inviter_id
		invitee_session.event_callback(
			f"[yellow]{inviter_session.player.name} invites you to a party. "
			f"Type [bold]accept[/bold] or [bold]decline[/bold].[/yellow]"
		)
		return [f"[dim]Invite sent to {invitee_session.player.name}.[/dim]"]

	def accept(self, character_id: int, world: WorldManager) -> list[str]:
		"""Accept a pending party invite."""
		inviter_id = self.invites.pop(character_id, None)
		if inviter_id is None:
			return ["[red]You have no pending party invite.[/red]"]

		inviter_session = world.sessions.get(inviter_id)
		accepter_session = world.sessions.get(character_id)
		if not inviter_session or not accepter_session:
			return ["[red]The inviter is no longer online.[/red]"]

		# Ensure/create party for the inviter
		leader = self._find_party_leader(inviter_id)
		if leader is None:
			leader = inviter_id
			self.parties[leader] = [inviter_id]

		if len(self.parties[leader]) >= MAX_PARTY_SIZE:
			return ["[red]The party is now full.[/red]"]

		self.parties[leader].append(character_id)

		# Notify all party members
		for mid in self.parties[leader]:
			session = world.sessions.get(mid)
			if session and mid != character_id:
				session.event_callback(f"[yellow]{accepter_session.player.name} joined the party.[/yellow]")

		return [f"[yellow]You joined {inviter_session.player.name}'s party.[/yellow]"]

	def decline(self, character_id: int, world: WorldManager) -> list[str]:
		"""Decline a pending party invite."""
		inviter_id = self.invites.pop(character_id, None)
		if inviter_id is None:
			return ["[red]You have no pending party invite.[/red]"]

		inviter_session = world.sessions.get(inviter_id)
		accepter_session = world.sessions.get(character_id)
		if inviter_session and accepter_session:
			inviter_session.event_callback(f"[dim]{accepter_session.player.name} declined your party invite.[/dim]")
		return ["[dim]Invite declined.[/dim]"]

	def leave_party(self, character_id: int, world: WorldManager) -> list[str]:
		"""Leave current party."""
		leader = self._find_party_leader(character_id)
		if leader is None:
			return ["[red]You are not in a party.[/red]"]

		members = self.parties[leader]
		session = world.sessions.get(character_id)
		player_name = session.player.name if session else "Someone"

		members.remove(character_id)

		# If leader left, promote next member or disband
		if character_id == leader:
			if len(members) >= 2:
				new_leader = members[0]
				self.parties[new_leader] = members
				del self.parties[leader]
				new_session = world.sessions.get(new_leader)
				if new_session:
					new_session.event_callback("[yellow]You are now the party leader.[/yellow]")
			elif len(members) == 1:
				# Solo — disband
				del self.parties[leader]
		elif len(members) == 1:
			# Only leader remains — disband
			del self.parties[leader]

		# Notify remaining members
		for mid in self.get_party_members(leader if leader != character_id else (members[0] if members else -1)):
			if mid == character_id:
				continue
			s = world.sessions.get(mid)
			if s:
				s.event_callback(f"[dim]{player_name} left the party.[/dim]")

		return ["[dim]You left the party.[/dim]"]

	def show_party(self, character_id: int, world: WorldManager) -> list[str]:
		"""Show current party members."""
		leader = self._find_party_leader(character_id)
		if leader is None:
			return ["[dim]You are not in a party.[/dim]"]

		messages = ["[bold]Party members:[/bold]"]
		for mid in self.parties[leader]:
			session = world.sessions.get(mid)
			name = session.player.name if session else "???"
			tag = " [yellow](leader)[/yellow]" if mid == leader else ""
			messages.append(f"  - {name}{tag}")
		return messages

	def remove_player(self, character_id: int, world: WorldManager) -> None:
		"""Silently remove a player from their party (disconnect cleanup)."""
		leader = self._find_party_leader(character_id)
		if leader is None:
			return
		self.invites.pop(character_id, None)
		self.leave_party(character_id, world)
