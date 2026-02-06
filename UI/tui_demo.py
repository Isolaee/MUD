"""
Interactive MUD Game TUI using Rich.

Launches a full-screen terminal UI with threaded keyboard input.
All game logic is dummy/placeholder — this is a UI test.

Run: python UI/tui_demo.py
"""

import msvcrt
import threading
import time

from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


# ---------------------------------------------------------------------------
# Dummy room data
# ---------------------------------------------------------------------------
ROOMS = {
    "cavern": (
        "[bold]Misty Cavern[/bold]\n"
        "\n"
        "You stand in a damp cavern. Water drips from\n"
        "stalactites above. The air is thick with mist.\n"
        "\n"
        "A [bold yellow]locked iron door[/bold yellow] blocks the way north.\n"
        "A narrow passage leads [cyan]east[/cyan].\n"
        "The path back goes [cyan]south[/cyan].\n"
        "\n"
    ),
    "forest": (
        "[bold]Darkwood Forest[/bold]\n"
        "\n"
        "Tall trees blot out the sky. The underbrush\n"
        "is thick and tangled. A faint trail winds north.\n"
        "\n"
        "Exits: [cyan]north[/cyan], [cyan]west[/cyan]."
    ),
    "clearing": (
        "[bold]Sunlit Clearing[/bold]\n"
        "\n"
        "A peaceful clearing bathed in sunlight.\n"
        "Wildflowers dot the grass.\n"
        "\n"
        "Exits: [cyan]south[/cyan], [cyan]east[/cyan]."
    ),
    "ruins": (
        "[bold]Ancient Ruins[/bold]\n"
        "\n"
        "Crumbling stone walls surround you. Vines\n"
        "creep over carved symbols you cannot read.\n"
        "\n"
        "Exits: [cyan]west[/cyan], [cyan]south[/cyan]."
    ),
}

# Simple movement graph: room -> {direction: room}
EXITS = {
    "cavern": {"south": "forest", "east": "ruins"},
    "forest": {"north": "cavern", "west": "clearing"},
    "clearing": {"east": "forest", "south": "ruins"},
    "ruins": {"west": "cavern", "north": "clearing"},
}

# Map art per room (player position changes)
MAP_ART = {
    "cavern": (
        "[dim]·  ·  ·  ·  ·[/dim]\n"
        "[dim]·[/dim]  [cyan]#[/cyan]──[cyan]#[/cyan]  [dim]·[/dim]\n"
        "[dim]·[/dim]  [dim]|[/dim]  [dim]|[/dim]  [dim]·[/dim]\n"
        "[dim]·[/dim]     [dim]|[/dim]  [dim]·[/dim]\n"
        "[dim]·[/dim]     [cyan]#[/cyan]  [dim]·[/dim]\n"
        "[dim]·  ·  ·  ·  ·[/dim]"
    ),
    "forest": (
        "[dim]·  ·  ·  ·  ·[/dim]\n"
        "[dim]·[/dim]  [cyan]#[/cyan]──[cyan]#[/cyan]  [dim]·[/dim]\n"
        "[dim]·[/dim]  [dim]|[/dim]  [dim]|[/dim]  [dim]·[/dim]\n"
        "[dim]·[/dim]  [cyan]#[/cyan]──[cyan]#[/cyan]  [dim]·[/dim]\n"
        "[dim]·[/dim]     [dim]|[/dim]  [dim]·[/dim]\n"
        "[dim]·[/dim]     [bold yellow]@[/bold yellow]  [dim]·[/dim]\n"
        "[dim]·  ·  ·  ·  ·[/dim]"
    ),
    "clearing": (
        "[dim]·  ·  ·  ·  ·[/dim]\n"

        "[dim]·[/dim]  [dim]|[/dim]  [dim]|[/dim]  [dim]·[/dim]\n"
        "[dim]·[/dim]  [cyan]#[/cyan]──[cyan]#[/cyan]  [dim]·[/dim]\n"
        "[dim]·[/dim]     [dim]|[/dim]  [dim]·[/dim]\n"
        "[dim]·[/dim]     [cyan]#[/cyan]  [dim]·[/dim]\n"
        "[dim]·  ·  ·  ·  ·[/dim]"
    ),
    "ruins": (
        "[dim]·  ·  ·  ·  ·[/dim]\n"
        "[dim]·[/dim]  [cyan]#[/cyan]──"
        "[bold yellow]@[/bold yellow]  [dim]·[/dim]\n"
        "[dim]·[/dim]  [dim]|[/dim]  [dim]|[/dim]  [dim]·[/dim]\n"
        "[dim]·[/dim]  [cyan]#[/cyan]──[cyan]#[/cyan]  [dim]·[/dim]\n"
        "[dim]·[/dim]     [dim]|[/dim]  [dim]·[/dim]\n"
        "[dim]·[/dim]     [cyan]#[/cyan]  [dim]·[/dim]\n"
        "[dim]·  ·  ·  ·  ·[/dim]"
    ),
}


# ---------------------------------------------------------------------------
# GameUI — mutable state + rendering
# ---------------------------------------------------------------------------
class GameUI:
    MAX_HISTORY = 50

    def __init__(self) -> None:
        self.running = True
        self.input_buffer = ""
        self.current_room = "cavern"
        self.event_history: list[str] = [
            "[dim]Welcome to the MUD! Type "
            "[bold]help[/bold] for commands.[/dim]",
            "[dim]You find yourself in a misty cavern...[/dim]",
        ]

    # -- command handling ---------------------------------------------------

    def dispatch(self, raw: str) -> None:
        cmd = raw.strip().lower()
        if not cmd:
            return

        if cmd in ("north", "south", "east", "west"):
            self._cmd_move(cmd)
        elif cmd == "look":
            self._cmd_look()
        elif cmd in ("inventory", "inv"):
            self._cmd_inventory()
        elif cmd == "help":
            self._cmd_help()
        elif cmd in ("quit", "exit"):
            self.running = False
        else:
            self.event_history.append(
                f"[red]Unknown command:[/red] {cmd}. "
                "Type [bold]help[/bold] for available commands."
            )

        self._trim_history()

    def _cmd_move(self, direction: str) -> None:
        exits = EXITS.get(self.current_room, {})
        if direction in exits:
            self.current_room = exits[direction]
            room_name = self.current_room.replace("_", " ").title()
            self.event_history.append(
                f"[dim]You walk {direction} to the {room_name}.[/dim]"
            )
        else:
            self.event_history.append(
                f"[yellow]You can't go {direction} from here.[/yellow]"
            )

    def _cmd_look(self) -> None:
        self.event_history.append("[dim]You look around...[/dim]")

    def _cmd_inventory(self) -> None:
        self.event_history.append("[dim]You rummage through your bag...[/dim]")

    def _cmd_help(self) -> None:
        self.event_history.append(
            "[bold]Commands:[/bold] north, south, east, west, "
            "look, inventory (inv), help, quit"
        )

    def _trim_history(self) -> None:
        if len(self.event_history) > self.MAX_HISTORY:
            cutoff = -self.MAX_HISTORY
            self.event_history = self.event_history[cutoff:]

    # -- panel builders -----------------------------------------------------

    def make_event_history(self) -> Panel:
        lines = "\n".join(self.event_history[-20:])
        return Panel(
            Text.from_markup(lines),
            title="[bold]Event History[/bold]",
            border_style="bright_blue",
            box=box.ROUNDED,
        )

    def make_current_events(self) -> Panel:
        room_text = ROOMS.get(self.current_room, "You are nowhere.")
        return Panel(
            Text.from_markup(room_text),
            title="[bold]Current Events[/bold]",
            border_style="green",
            box=box.ROUNDED,
        )

    def make_writing_interface(self) -> Panel:
        return Panel(
            Text.from_markup(f"> {self.input_buffer}█"),
            title="[bold]Command[/bold]",
            border_style="white",
            box=box.ROUNDED,
            height=3,
        )

    def make_map(self) -> Panel:
        art = MAP_ART.get(self.current_room, "")
        return Panel(
            Text.from_markup(art),
            title="[bold]Map[/bold]",
            border_style="yellow",
            box=box.ROUNDED,
        )

    def make_stats(self) -> Panel:
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("stat", style="bold")
        table.add_column("value", justify="right")
        table.add_row("HP", "[red]45[/red] / 60")
        table.add_row("MP", "[blue]20[/blue] / 20")
        table.add_row("STR", "14")
        table.add_row("DEX", "12")
        table.add_row("INT", "10")
        table.add_row("Level", "[bold]3[/bold]")
        table.add_row("XP", "230 / 500")
        return Panel(
            table,
            title="[bold]Stats[/bold]",
            border_style="red",
            box=box.ROUNDED,
        )

    def make_inventory(self) -> Panel:
        items = Text.from_markup(
            "[white]1.[/white] Iron Sword\n"
            "[white]2.[/white] Leather Armor\n"
            "[white]3.[/white] Health Potion [dim]x3[/dim]\n"
            "[white]4.[/white] [bold yellow]Silver Key[/bold yellow]\n"
            "[white]5.[/white] Torch [dim]x2[/dim]\n"
            "\n"
            "[dim]Gold: 47[/dim]"
        )
        return Panel(
            items,
            title="[bold]Inventory[/bold]",
            border_style="magenta",
            box=box.ROUNDED,
        )

    # -- layout builder -----------------------------------------------------

    def build_layout(self) -> Layout:
        layout = Layout()
        layout.split_row(
            Layout(name="left", ratio=1),
            Layout(name="middle", ratio=3),
            Layout(name="right", ratio=1),
        )
        layout["middle"].split_column(
            Layout(name="current_events", ratio=1),
            Layout(name="writing", size=3),
        )
        layout["right"].split_column(
            Layout(name="map", ratio=1),
            Layout(name="stats", ratio=1),
            Layout(name="inventory", ratio=1),
        )

        layout["left"].update(self.make_event_history())
        layout["current_events"].update(self.make_current_events())
        layout["writing"].update(self.make_writing_interface())
        layout["map"].update(self.make_map())
        layout["stats"].update(self.make_stats())
        layout["inventory"].update(self.make_inventory())

        return layout


# ---------------------------------------------------------------------------
# Input thread — reads keystrokes via msvcrt (Windows)
# ---------------------------------------------------------------------------
def input_loop(ui: GameUI) -> None:
    while ui.running:
        if msvcrt.kbhit():
            ch = msvcrt.getwch()

            if ch == "\r":  # Enter
                ui.dispatch(ui.input_buffer)
                ui.input_buffer = ""
            elif ch == "\x08":  # Backspace
                ui.input_buffer = ui.input_buffer[:-1]
            elif ch == "\x1b":  # Escape — ignore
                pass
            elif ch in ("\x00", "\xe0"):  # Special key prefix — consume next
                msvcrt.getwch()
            elif ch.isprintable():
                ui.input_buffer += ch
        else:
            time.sleep(0.02)


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------
def main() -> None:
    console = Console()
    ui = GameUI()

    thread = threading.Thread(target=input_loop, args=(ui,), daemon=True)
    thread.start()

    with Live(
        ui.build_layout(),
        console=console,
        refresh_per_second=4,
        screen=True,
    ) as live:
        while ui.running:
            live.update(ui.build_layout())
            time.sleep(0.1)

    console.clear()
    console.print("[bold]Thanks for playing! Goodbye.[/bold]")


if __name__ == "__main__":
    main()
