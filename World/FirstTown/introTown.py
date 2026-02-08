"""Intro town — the first proper settlement the player encounters.

Currently contains a single town-square room.  Additional buildings,
NPCs, and shops will be added here as the game grows.
"""

from Objects.room import Room, Description

square = Room("Town square")
square.description = Description(
	short="Wide Town square.",
	long="A large town square filled with people.",
)
