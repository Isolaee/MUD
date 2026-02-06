"""
Interactive MUD Game TUI using Rich.

Launches a full-screen terminal UI with threaded keyboard input.
Uses Room objects from World.demoArea for game data.

Run: python -m UI.tui_demo
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

from Objects.room import Room
from World.demoArea import START_ROOM


# ---------------------------------------------------------------
# GameUI — mutable state + rendering
# ---------------------------------------------------------------
class GameUI:
    MAX_HISTORY = 50

    def __init__(self, start: Room) -> None:
        self.running = True
        self.input_buffer = ""
        self.current_room: Room = start
        self.event_history: list[str] = [
            "[dim]Welcome to the MUD! Type "
            "[bold]help[/bold] for commands.[/dim]",
        ]
        self._cmd_look()

    # -- command handling ------------------------------------

    def dispatch(self, raw: str) -> None:
        cmd = raw.strip().lower()
        if not cmd:
            return

        if cmd == "look":
            self._cmd_look()
        elif cmd in ("inventory", "inv"):
            self._cmd_inventory()
        elif cmd == "help":
            self._cmd_help()
        elif cmd in ("quit", "exit"):
            self.running = False
        else:
            self._cmd_go(cmd)

        self._trim_history()

    def _cmd_go(self, target: str) -> None:
        target_lower = target.lower()
        connections = self.current_room.connected_rooms
        for direction, room in connections.items():
            if room.name.lower() == target_lower:
                self.current_room = room
                self.event_history.append(
                    "[dim]You move "
                    f"{direction.name.replace('_', ' ').lower()}"
                    f" to {room.name}.[/dim]"
                )
                self._cmd_look()
                return
        self.event_history.append(
            f"[red]Unknown command:[/red] {target}. "
            "Type [bold]help[/bold] for commands."
        )

    def _cmd_look(self) -> None:
        desc = self.current_room.description
        if desc and desc.long:
            self.event_history.append(
                f"[dim]{desc.long}[/dim]"
            )
        elif desc:
            self.event_history.append(
                f"[dim]{desc.short}[/dim]"
            )

    def _cmd_inventory(self) -> None:
        items = self.current_room.present_items
        if not items:
            self.event_history.append(
                "[dim]Nothing here.[/dim]"
            )
            return
        for item in items:
            self.event_history.append(
                f"  [white]- {item.name}[/white]"
            )

    def _cmd_help(self) -> None:
        connections = self.current_room.connected_rooms
        exits = ", ".join(
            f"{r.name} ({d.name.replace('_', ' ').lower()})"
            for d, r in connections.items()
        )
        self.event_history.append(
            "[bold]Commands:[/bold] look, "
            "inventory (inv), help, quit"
        )
        if exits:
            self.event_history.append(
                f"[bold]Go to:[/bold] {exits}"
            )

    def _trim_history(self) -> None:
        if len(self.event_history) > self.MAX_HISTORY:
            cutoff = -self.MAX_HISTORY
            self.event_history = self.event_history[cutoff:]

    # -- panel builders --------------------------------------

    def make_event_history(self) -> Panel:
        lines = "\n".join(self.event_history[-20:])
        return Panel(
            Text.from_markup(lines),
            title="[bold]Event History[/bold]",
            border_style="bright_blue",
            box=box.ROUNDED,
        )

    def make_current_events(self) -> Panel:
        room = self.current_room
        desc = room.description
        parts = [f"[bold]{room.name}[/bold]\n"]
        if desc:
            parts.append(desc.long or desc.short)
        exits = ", ".join(
            f"[cyan]{r.name}[/cyan]"
            f" ({d.name.replace('_', ' ').lower()})"
            for d, r in room.connected_rooms.items()
        )
        if exits:
            parts.append(f"\nExits: {exits}")
        items = room.present_items
        if items:
            parts.append("\n[yellow]Items here:[/yellow]")
            for item in items:
                parts.append(f"  - {item.name}")
        return Panel(
            Text.from_markup("\n".join(parts)),
            title="[bold]Current Events[/bold]",
            border_style="green",
            box=box.ROUNDED,
        )

    def make_writing_interface(self) -> Panel:
        return Panel(
            Text.from_markup(
                f"> {self.input_buffer}\u2588"
            ),
            title="[bold]Command[/bold]",
            border_style="white",
            box=box.ROUNDED,
            height=3,
        )

    def make_map(self) -> Panel:
        return Panel(
            Text.from_markup("[dim]No map data[/dim]"),
            title="[bold]Map[/bold]",
            border_style="yellow",
            box=box.ROUNDED,
        )

    def make_stats(self) -> Panel:
        table = Table(
            show_header=False, box=None, padding=(0, 1)
        )
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
        items = self.current_room.present_items
        if items:
            lines = "\n".join(
                f"[white]{i + 1}.[/white] {item.name}"
                for i, item in enumerate(items)
            )
        else:
            lines = "[dim]Nothing here.[/dim]"
        return Panel(
            Text.from_markup(lines),
            title="[bold]Inventory[/bold]",
            border_style="magenta",
            box=box.ROUNDED,
        )

    # -- layout builder --------------------------------------

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
        layout["current_events"].update(
            self.make_current_events()
        )
        layout["writing"].update(
            self.make_writing_interface()
        )
        layout["map"].update(self.make_map())
        layout["stats"].update(self.make_stats())
        layout["inventory"].update(self.make_inventory())

        return layout


# ---------------------------------------------------------------
# Input thread — reads keystrokes via msvcrt (Windows)
# ---------------------------------------------------------------
def input_loop(ui: GameUI) -> None:
    while ui.running:
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch == "\r":
                ui.dispatch(ui.input_buffer)
                ui.input_buffer = ""
            elif ch == "\x08":
                ui.input_buffer = ui.input_buffer[:-1]
            elif ch == "\x1b":
                pass
            elif ch in ("\x00", "\xe0"):
                msvcrt.getwch()
            elif ch.isprintable():
                ui.input_buffer += ch
        else:
            time.sleep(0.02)


# ---------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------
def main() -> None:
    console = Console()
    ui = GameUI(START_ROOM)

    thread = threading.Thread(
        target=input_loop, args=(ui,), daemon=True
    )
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
    console.print(
        "[bold]Thanks for playing! Goodbye.[/bold]"
    )


if __name__ == "__main__":
    main()
