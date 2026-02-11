"""MUD Game — application entry point.

Launches the TUI, optionally skipping to a specific view and room.

Usage:
    python app.py                          # normal start (character creation)
    python app.py GameUI "Room Intro"      # jump straight into a room
    python app.py GameUI                   # jump to GameUI with default start room
"""

import sys

from UI.app_engine import Application


def _find_room(name: str):
	"""Walk every room reachable from START_ROOM and return the first name match."""
	from collections import deque

	from World.demoArea import START_ROOM

	queue = deque([START_ROOM])
	seen: set = {START_ROOM}
	while queue:
		room = queue.popleft()
		if room.name.lower() == name.lower():
			return room
		for neighbor in room.connected_rooms.values():
			if neighbor not in seen:
				seen.add(neighbor)
				queue.append(neighbor)

	available = ", ".join(f'"{r.name}"' for r in seen)
	print(f'Error: room "{name}" not found.\nAvailable rooms: {available}')
	sys.exit(1)


def _build_initial_view(args: list[str]):
	"""Return the starting View based on CLI arguments."""
	if not args:
		from UI.characterCreation.characterCreation_ui import CharacterCreationUI

		return CharacterCreationUI()

	view_name = args[0]

	if view_name == "GameUI":
		from UI.in_game_ui.gameUI import GameUI
		from World.demoArea import START_ROOM

		room = _find_room(args[1]) if len(args) > 1 else START_ROOM
		return GameUI(room)

	if view_name == "CharacterCreationUI":
		from UI.characterCreation.characterCreation_ui import CharacterCreationUI

		return CharacterCreationUI()

	print(f'Error: unknown view "{view_name}".')
	print("Available views: GameUI, CharacterCreationUI")
	sys.exit(1)


if __name__ == "__main__":
	view = _build_initial_view(sys.argv[1:])
	app = Application(view)
	app.run()
