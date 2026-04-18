# MUD — Terminal RPG Engine

## Overview
A Python-based terminal RPG with character creation, a room-based open world, a quest system, and an inventory/equipment system. Rendered in the terminal using Rich for a clean TUI experience. Designed to support multiplayer over SSH in future iterations.

## Problem It Solves
- Building an extensible RPG engine from scratch is a useful exercise in OOP design, TUI development, and game architecture
- Text-based MUDs are a timeless format for collaborative storytelling that can run on any machine without a GPU
- Target users: players who enjoy text-based RPGs; developers studying Python game engine patterns

## Use Cases
1. A new player launches the game, walks through character creation (name, race, class), and enters the starting town to pick up their first quest
2. A developer adds a new room by creating a `Room` object in the world module and connecting it to existing rooms via `connected_rooms` — no engine changes needed
3. A quest author writes a new quest in `Quests/` with objectives, requirements, and rewards, then wires it into the world; it becomes available to any character who meets the requirements

## Key Features
- **Character creation** — name, race (`characterRaces`), and class (`characterClasses`) selection via interactive TUI
- **Room-based navigation** — rooms are Python objects with named exits pointing to adjacent rooms
- **Quest system** — quests have objectives, requirements, and rewards; tracked per character
- **Item and equipment system** — weapons (swords, daggers) with base classes for extensibility
- **Rich TUI** — terminal UI built with the `rich` library; supports colour, panels, and structured layouts
- **SSH multiplayer foundation** — `asyncssh` is in the dependency list for future server mode

## Tech Stack
| Component | Technology |
|---|---|
| Language | Python 3.10+ |
| TUI | Rich |
| Async / Networking | asyncssh (future multiplayer) |
| Testing | pytest |
| Linting | Ruff |

## Getting Started

```bash
# 1. Clone the repo
git clone https://github.com/Isolaee/MUD.git
cd MUD

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the game
python app.py                          # start from character creation
python app.py GameUI "Room Intro"      # jump directly into a room (dev shortcut)
python app.py GameUI                   # jump to game UI with the default start room
```

### Running tests
```bash
pytest
```

### Project structure
```
app.py              — entry point
Objects/            — Characters, Items, Rooms base classes
Quests/             — Quest, Objective, Reward definitions
UI/                 — TUI screens (character creation, game UI)
World/              — Room graph and demo area
logic/              — Game loop and command processing
server/             — Future SSH server module
```
