"""Turn-based combat system.

Combat is initiated by ``attack [target]`` and creates a CombatInstance
that tracks combatants, turn order (initiative), and round state.

During combat the CommandDispatcher routes player input here instead of
through the normal action pipeline.  NPCs act automatically on their turn.

Key design points:
- State lives in CombatManager (owned by WorldManager) so it is shared.
- Single-threaded asyncio means no locks are needed.
- 30-second turn timer auto-skips idle players.
- Party members in the same room are pulled into combat automatically.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from Objects.Characters.character import CharacterType

if TYPE_CHECKING:
	from Objects.Characters.character import Character
	from Objects.Items.weapons import Weapon
	from Objects.Rooms.room import Room
	from server.world_manager import WorldManager

TURN_TIMEOUT_SECONDS = 30
KNOCKOUT_RECOVERY_SECONDS = 60


@dataclass
class Combatant:
	"""A single participant in a combat encounter."""

	character_id: int
	character: Character
	team: int  # 0 = attackers, 1 = defenders
	is_defending: bool = False
	is_knocked_out: bool = False
	is_npc: bool = False
	initiative: int = 0


@dataclass
class CombatInstance:
	"""Represents one ongoing combat encounter in a room."""

	combatants: list[Combatant] = field(default_factory=list)
	current_turn_index: int = 0
	room: Room | None = None
	turn_timer_task: asyncio.Task | None = None
	round_number: int = 1

	@property
	def current_combatant(self) -> Combatant | None:
		if not self.combatants:
			return None
		active = [c for c in self.combatants if not c.is_knocked_out]
		if not active:
			return None
		idx = self.current_turn_index % len(active)
		return active[idx]

	def get_active_combatants(self) -> list[Combatant]:
		return [c for c in self.combatants if not c.is_knocked_out]

	def get_enemies(self, combatant: Combatant) -> list[Combatant]:
		return [c for c in self.combatants if c.team != combatant.team and not c.is_knocked_out]

	def is_over(self) -> bool:
		"""Combat ends when one side has no active combatants."""
		teams = set()
		for c in self.combatants:
			if not c.is_knocked_out:
				teams.add(c.team)
		return len(teams) <= 1


class CombatManager:
	"""Manages all active combats across the game world."""

	def __init__(self) -> None:
		# character_id -> CombatInstance they are in
		self.active_combats: dict[int, CombatInstance] = {}

	def is_in_combat(self, character_id: int) -> bool:
		return character_id in self.active_combats

	def start_combat(
		self,
		attacker_id: int,
		target: Character,
		room: Room,
		world: WorldManager,
	) -> list[str]:
		"""Initiate combat between the attacker (and party) vs target (and party).

		Returns messages for the attacker's event log.
		"""
		attacker_session = world.sessions.get(attacker_id)
		if not attacker_session:
			return ["[red]Error starting combat.[/red]"]

		if self.is_in_combat(attacker_id):
			return ["[red]You are already in combat![/red]"]

		# Build combatant lists
		combat = CombatInstance(room=room)

		# --- Team 0: attackers (player + party members in room) ---
		attacker_ids = world.party_manager.get_party_members_in_room(attacker_id, room.uid, world)
		# Ensure the attacker is included
		if attacker_id not in attacker_ids:
			attacker_ids.insert(0, attacker_id)

		for aid in attacker_ids:
			if self.is_in_combat(aid):
				continue
			session = world.sessions.get(aid)
			if session:
				c = Combatant(
					character_id=aid,
					character=session.player,
					team=0,
					is_npc=False,
				)
				combat.combatants.append(c)

		# --- Team 1: defenders ---
		target_is_player = target.object_type() == CharacterType.PLAYER
		if target_is_player:
			# Find the target's character_id from sessions
			target_id = None
			for cid, session in world.sessions.items():
				if session.player is target:
					target_id = cid
					break
			if target_id is None:
				return ["[red]Target not found.[/red]"]

			if self.is_in_combat(target_id):
				return [f"[red]{target.name} is already in combat![/red]"]

			defender_ids = world.party_manager.get_party_members_in_room(target_id, room.uid, world)
			if target_id not in defender_ids:
				defender_ids.insert(0, target_id)

			for did in defender_ids:
				if self.is_in_combat(did):
					continue
				session = world.sessions.get(did)
				if session:
					c = Combatant(
						character_id=did,
						character=session.player,
						team=1,
						is_npc=False,
					)
					combat.combatants.append(c)
		else:
			# NPC target — use uid hash as character_id
			npc_id = hash(target.uid) & 0x7FFFFFFF
			c = Combatant(
				character_id=npc_id,
				character=target,
				team=1,
				is_npc=True,
			)
			combat.combatants.append(c)

		if len(combat.combatants) < 2:
			return ["[red]Cannot start combat.[/red]"]

		# Roll initiative and sort
		self._roll_initiative(combat)

		# Register all combatants
		for c in combat.combatants:
			self.active_combats[c.character_id] = combat

		# Broadcast combat start
		attacker_name = attacker_session.player.name
		target_name = target.name
		world.broadcast_to_room(
			room,
			f"[bold red]Combat begins! {attacker_name} attacks {target_name}![/bold red]",
		)

		# Show turn order
		order_str = ", ".join(f"{c.character.name}({c.initiative})" for c in combat.combatants)
		world.broadcast_to_room(room, f"[dim]Turn order: {order_str}[/dim]")

		# Start first turn
		self._start_turn(combat, world)

		return []

	def handle_combat_input(self, character_id: int, raw_input: str, world: WorldManager) -> list[str]:
		"""Process a combat command from a player.

		Returns messages for the player's event log.
		"""
		combat = self.active_combats.get(character_id)
		if not combat:
			return ["[red]You are not in combat.[/red]"]

		current = combat.current_combatant
		if not current or current.character_id != character_id:
			return ["[dim]It's not your turn.[/dim]"]

		# Cancel the turn timer
		self._cancel_timer(combat)

		cmd = raw_input.strip().lower()
		parts = cmd.split(None, 1)
		action = parts[0] if parts else ""
		arg = parts[1] if len(parts) > 1 else ""

		if action in ("attack", "atk", "a"):
			return self._handle_attack(current, arg, combat, world)
		elif action in ("defend", "def", "d"):
			return self._handle_defend(current, combat, world)
		elif action in ("flee", "run", "f"):
			return self._handle_flee(current, combat, world)
		else:
			return [
				"[yellow]Combat actions: [bold]attack[/bold] [target], [bold]defend[/bold], [bold]flee[/bold][/yellow]"
			]

	# -- internal mechanics ---------------------------------------------------

	def _roll_initiative(self, combat: CombatInstance) -> None:
		"""Roll initiative for all combatants and sort by descending roll."""
		for c in combat.combatants:
			roll = random.randint(1, 20)
			modifier = c.character.stamina // 10
			c.initiative = roll + modifier
		combat.combatants.sort(key=lambda c: c.initiative, reverse=True)

	def _get_weapon(self, character: Character) -> Weapon | None:
		"""Return the character's equipped weapon, or None (fists)."""
		return getattr(character, "equipped_weapon", None)

	def _calculate_damage(self, attacker: Combatant, defender: Combatant) -> tuple[int, bool]:
		"""Calculate attack damage. Returns (damage, did_hit)."""
		weapon = self._get_weapon(attacker.character)
		hit_chance = weapon.hitChance if weapon else 0.75

		if random.random() > hit_chance:
			return 0, False

		base = attacker.character.base_attack
		bonus = weapon.attackBonus if weapon else 0
		variance = random.randint(-2, 2)
		damage = max(1, base + bonus + variance)

		# Defending halves damage
		if defender.is_defending:
			damage = max(1, damage // 2)

		return damage, True

	def _handle_attack(
		self, attacker: Combatant, target_name: str, combat: CombatInstance, world: WorldManager
	) -> list[str]:
		"""Execute an attack action."""
		enemies = combat.get_enemies(attacker)
		if not enemies:
			self._end_combat(combat, world)
			return ["[dim]No enemies remain.[/dim]"]

		# Resolve target
		defender = None
		if target_name:
			for e in enemies:
				if e.character.name.lower() == target_name.lower():
					defender = e
					break
			if defender is None:
				return [
					f"[red]'{target_name}' is not a valid target. Enemies: {', '.join(e.character.name for e in enemies)}[/red]"
				]
		else:
			# Default to first enemy
			defender = enemies[0]

		damage, did_hit = self._calculate_damage(attacker, defender)

		if did_hit:
			defender.character.hp -= damage
			weapon = self._get_weapon(attacker.character)
			weapon_name = weapon.name if weapon else "fists"
			msg = (
				f"[bold]{attacker.character.name}[/bold] hits "
				f"[bold]{defender.character.name}[/bold] with {weapon_name} "
				f"for [red]{damage}[/red] damage! "
				f"({defender.character.name}: {max(0, defender.character.hp)} HP)"
			)
			world.broadcast_to_room(combat.room, msg)

			# Check knockout
			if defender.character.hp <= 0:
				defender.character.hp = 0
				defender.is_knocked_out = True
				defender.character.is_knocked_out = True
				world.broadcast_to_room(
					combat.room,
					f"[bold red]{defender.character.name} is knocked out![/bold red]",
				)
				if not defender.is_npc:
					self._start_knockout_recovery(defender, world)
		else:
			msg = f"[bold]{attacker.character.name}[/bold] attacks [bold]{defender.character.name}[/bold] but misses!"
			world.broadcast_to_room(combat.room, msg)

		# Reset defending from last round
		attacker.is_defending = False

		# Check if combat is over
		if combat.is_over():
			self._end_combat(combat, world)
			return []

		self._advance_turn(combat, world)
		return []

	def _handle_defend(self, combatant: Combatant, combat: CombatInstance, world: WorldManager) -> list[str]:
		"""Execute a defend action — halves incoming damage until next turn."""
		combatant.is_defending = True
		world.broadcast_to_room(
			combat.room,
			f"[bold]{combatant.character.name}[/bold] takes a defensive stance.",
		)

		if combat.is_over():
			self._end_combat(combat, world)
			return []

		self._advance_turn(combat, world)
		return []

	def _handle_flee(self, combatant: Combatant, combat: CombatInstance, world: WorldManager) -> list[str]:
		"""Attempt to flee combat. 50% chance of success."""
		if random.random() < 0.5:
			# Success — remove from combat
			world.broadcast_to_room(
				combat.room,
				f"[bold]{combatant.character.name}[/bold] flees from combat!",
			)
			self._remove_combatant(combatant, combat, world)

			if combat.is_over():
				self._end_combat(combat, world)
				return ["[dim]You escaped![/dim]"]

			self._advance_turn(combat, world)
			return ["[dim]You escaped![/dim]"]
		else:
			world.broadcast_to_room(
				combat.room,
				f"[bold]{combatant.character.name}[/bold] tries to flee but fails!",
			)
			combatant.is_defending = False
			self._advance_turn(combat, world)
			return []

	def _npc_take_turn(self, combatant: Combatant, combat: CombatInstance, world: WorldManager) -> None:
		"""Simple NPC AI — attacks a random enemy."""
		enemies = combat.get_enemies(combatant)
		if not enemies:
			return

		target = random.choice(enemies)
		self._handle_attack(combatant, target.character.name, combat, world)

	def _advance_turn(self, combat: CombatInstance, world: WorldManager) -> None:
		"""Move to the next active combatant."""
		active = combat.get_active_combatants()
		if not active:
			self._end_combat(combat, world)
			return

		combat.current_turn_index = (combat.current_turn_index + 1) % len(active)

		# Check for new round
		if combat.current_turn_index == 0:
			combat.round_number += 1
			world.broadcast_to_room(
				combat.room,
				f"[dim]--- Round {combat.round_number} ---[/dim]",
			)

		self._start_turn(combat, world)

	def _start_turn(self, combat: CombatInstance, world: WorldManager) -> None:
		"""Begin the current combatant's turn."""
		current = combat.current_combatant
		if current is None:
			self._end_combat(combat, world)
			return

		if current.is_npc:
			self._npc_take_turn(current, combat, world)
			return

		# Notify the player it's their turn
		session = world.sessions.get(current.character_id)
		if session:
			enemies = combat.get_enemies(current)
			enemy_list = ", ".join(f"{e.character.name} ({e.character.hp}hp)" for e in enemies)
			session.event_callback(f"[bold yellow]Your turn![/bold yellow] Enemies: {enemy_list}")
			session.event_callback(
				"[yellow]Actions: [bold]attack[/bold] [target], [bold]defend[/bold], [bold]flee[/bold][/yellow]"
			)

		# Start 30s timer
		self._start_timer(current.character_id, combat, world)

	def _start_timer(self, character_id: int, combat: CombatInstance, world: WorldManager) -> None:
		"""Start the 30-second turn timer."""
		self._cancel_timer(combat)

		async def _timeout():
			await asyncio.sleep(TURN_TIMEOUT_SECONDS)
			self._on_turn_timeout(character_id, combat, world)

		try:
			loop = asyncio.get_running_loop()
			combat.turn_timer_task = loop.create_task(_timeout())
		except RuntimeError:
			# No running event loop (e.g. in tests) — skip timer
			pass

	def _cancel_timer(self, combat: CombatInstance) -> None:
		"""Cancel the current turn timer if any."""
		if combat.turn_timer_task and not combat.turn_timer_task.done():
			combat.turn_timer_task.cancel()
			combat.turn_timer_task = None

	def _on_turn_timeout(self, character_id: int, combat: CombatInstance, world: WorldManager) -> None:
		"""Handle turn timeout — auto-skip the player's turn."""
		current = combat.current_combatant
		if current and current.character_id == character_id:
			session = world.sessions.get(character_id)
			if session:
				session.event_callback("[red]Turn timed out![/red]")
			world.broadcast_to_room(
				combat.room,
				f"[dim]{current.character.name} hesitates...[/dim]",
			)
			current.is_defending = False
			self._advance_turn(combat, world)

	def _remove_combatant(self, combatant: Combatant, combat: CombatInstance, world: WorldManager) -> None:
		"""Remove a combatant from combat (flee or disconnect)."""
		# Adjust turn index if needed
		active = combat.get_active_combatants()
		try:
			removed_idx = active.index(combatant)
			if removed_idx < combat.current_turn_index:
				combat.current_turn_index -= 1
		except ValueError:
			pass

		combat.combatants.remove(combatant)
		self.active_combats.pop(combatant.character_id, None)

	def _end_combat(self, combat: CombatInstance, world: WorldManager) -> None:
		"""End combat and clean up."""
		self._cancel_timer(combat)

		# Determine winners
		active = combat.get_active_combatants()
		if active:
			winning_team = active[0].team
			winners = [c for c in active if c.team == winning_team]
			winner_names = ", ".join(c.character.name for c in winners)
			world.broadcast_to_room(
				combat.room,
				f"[bold green]Combat is over! {winner_names} victorious![/bold green]",
			)
		else:
			world.broadcast_to_room(
				combat.room,
				"[bold]Combat is over! No one left standing.[/bold]",
			)

		# Unregister all combatants
		for c in combat.combatants:
			self.active_combats.pop(c.character_id, None)

	def _start_knockout_recovery(self, combatant: Combatant, world: WorldManager) -> None:
		"""Start a 60-second recovery timer for a knocked-out player."""

		async def _recover():
			await asyncio.sleep(KNOCKOUT_RECOVERY_SECONDS)
			combatant.character.hp = 1
			combatant.character.is_knocked_out = False
			combatant.is_knocked_out = False
			session = world.sessions.get(combatant.character_id)
			if session:
				session.event_callback("[green]You regain consciousness with 1 HP.[/green]")

		try:
			loop = asyncio.get_running_loop()
			loop.create_task(_recover())
		except RuntimeError:
			# No event loop (tests) — just restore immediately
			combatant.character.hp = 1
			combatant.character.is_knocked_out = False

	def remove_player(self, character_id: int, world: WorldManager) -> None:
		"""Remove a player from combat (disconnect cleanup)."""
		combat = self.active_combats.get(character_id)
		if not combat:
			return

		for c in combat.combatants:
			if c.character_id == character_id:
				c.is_knocked_out = True
				self._remove_combatant(c, combat, world)
				world.broadcast_to_room(
					combat.room,
					f"[dim]{c.character.name} has left combat.[/dim]",
				)
				break

		if combat.is_over():
			self._end_combat(combat, world)
