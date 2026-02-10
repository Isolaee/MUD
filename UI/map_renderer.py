"""BFS room traversal and ASCII map rendering.

Generates a small overhead map of the rooms surrounding the player.
The algorithm:

1. **BFS discovery** — walk the room graph up to *MAX_DEPTH* hops,
   assigning each room a (dx, dy) grid position.
2. **Grid placement** — each room is drawn as a 3-line ASCII box
   on a fixed character grid.
3. **Path drawing** — connections between adjacent rooms are rendered
   with ``|``, ``--``, ``/``, or ``\\`` characters.

The current room is highlighted with ``@@`` in bold yellow; other
rooms are shown in cyan with the first two letters of their name.
"""

from __future__ import annotations

from collections import deque

from rich import box
from rich.panel import Panel
from rich.text import Text

from Objects.room import Room, DIR_VECTOR


class MapRenderer:
	"""BFS-based ASCII map renderer."""

	GRID_WIDTH = 30
	GRID_HEIGHT = 19
	MAX_DEPTH = 2

	def __init__(self, current_room: Room) -> None:
		self._room = current_room

	def build(self) -> Panel:
		"""Build the ASCII map panel showing nearby rooms and connections."""
		positions, edges = self._bfs_rooms()
		g = [[" "] * self.GRID_WIDTH for _ in range(self.GRID_HEIGHT)]

		# Draw room boxes
		for room, (dx, dy) in positions.items():
			col, row = self._grid_pos(dx, dy)
			if room == self._room:
				self._place_box(g, col, row, "@@", "bold yellow")
			else:
				self._place_box(g, col, row, room.name, "cyan")

		# Draw connection paths
		for edge in edges:
			p1, p2 = tuple(edge)
			self._draw_path(g, p1, p2)

		out = "\n".join("".join(row) for row in g)
		return Panel(
			Text.from_markup(out),
			title="[bold]Map[/bold]",
			border_style="yellow",
			box=box.ROUNDED,
		)

	def _bfs_rooms(self):
		"""Discover rooms reachable within MAX_DEPTH hops via BFS.

		Returns:
			positions: dict mapping Room -> (dx, dy) grid coordinate.
			edges: set of frozenset pairs representing connections to draw.
		"""
		positions = {self._room: (0, 0)}
		occupied = {(0, 0): self._room}
		edges: set = set()
		queue = deque([(self._room, 0)])
		visited = {self._room}

		while queue:
			room, depth = queue.popleft()
			room_pos = positions[room]
			if depth >= self.MAX_DEPTH:
				continue
			for d, neighbor in room.connected_rooms.items():
				dx, dy = DIR_VECTOR[d]
				npos = (room_pos[0] + dx, room_pos[1] + dy)
				if neighbor not in positions:
					if abs(npos[0]) > 2 or abs(npos[1]) > 2:
						continue
					if npos in occupied:
						continue
					positions[neighbor] = npos
					occupied[npos] = neighbor
				p1 = positions[room]
				p2 = positions.get(neighbor)
				if p2 is not None:
					edges.add(frozenset((p1, p2)))
				if neighbor not in visited:
					visited.add(neighbor)
					queue.append((neighbor, depth + 1))

		return positions, edges

	@staticmethod
	def _grid_pos(dx, dy):
		"""Convert a room grid coordinate (dx, dy) to character-grid (col, row)."""
		col = (dx + 2) * 6
		row = (dy + 2) * 4
		return col, row

	@staticmethod
	def _place_box(g, col, row, label, style):
		"""Draw a 3-line ASCII room box at (col, row) on the character grid."""
		s, e = f"[{style}]", f"[/{style}]"
		g[row][col] = f"{s}+--+{e}"
		g[row + 1][col] = f"{s}|{e}{label[:2]}{s}|{e}"
		g[row + 2][col] = f"{s}+--+{e}"
		for r in range(row, row + 3):
			for c in range(col + 1, col + 4):
				if c < len(g[0]):
					g[r][c] = ""

	@staticmethod
	def _draw_path(g, p1, p2):
		"""Draw a connector character between two adjacent room positions."""
		ddx = p2[0] - p1[0]
		ddy = p2[1] - p1[1]
		if abs(ddx) > 1 or abs(ddy) > 1:
			return
		c1, r1 = MapRenderer._grid_pos(*p1)
		if ddx == 0 and ddy == -1:
			g[r1 - 1][c1 + 1] = "[dim]|[/dim]"
		elif ddx == 0 and ddy == 1:
			g[r1 + 3][c1 + 1] = "[dim]|[/dim]"
		elif ddx == 1 and ddy == 0:
			g[r1 + 1][c1 + 4] = "[dim]--[/dim]"
		elif ddx == -1 and ddy == 0:
			g[r1 + 1][c1 - 2] = "[dim]--[/dim]"
		elif ddx == 1 and ddy == -1:
			g[r1 - 1][c1 + 4] = "[dim]/[/dim]"
		elif ddx == -1 and ddy == -1:
			g[r1 - 1][c1 - 1] = "[dim]\\[/dim]"
		elif ddx == 1 and ddy == 1:
			g[r1 + 3][c1 + 4] = "[dim]\\[/dim]"
		elif ddx == -1 and ddy == 1:
			g[r1 + 3][c1 - 1] = "[dim]/[/dim]"
