"""MUD Game — application entry point.

Launches the TUI starting with the character creation screen.

Run: python app.py
"""

from UI.app_engine import Application
from UI.characterCreation.characterCreation_ui import CharacterCreationUI

if __name__ == "__main__":
	app = Application(CharacterCreationUI())
	app.run()
