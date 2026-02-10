"""
MUD Game — application entry point.

Connects the UI to the world by loading the demo area
and launching the TUI.

Run: python app.py
"""

from UI.game_ui import main as start_ui
from World.demoArea import START_ROOM  ## Delete afte implaementing character creation

if __name__ == "__main__":
	start_ui(START_ROOM)
