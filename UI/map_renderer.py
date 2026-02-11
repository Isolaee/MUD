"""BFS room traversal and simple ASCII map rendering.

Generates an overhead map of all rooms in the connected area.

Symbols:
- ``@`` — current room
- ``#`` — visited room
- ``O`` — unvisited room
- ``-``, ``|``, ``/``, ``\\`` — connections
"""

from __future__ import annotations

from collections import deque

from rich import box
from rich.panel import Panel
from rich.text import Text

from Objects.room import Room, DIR_VECTOR


class MapRenderer:
	"""BFS-based ASCII map renderer using simple symbols."""

	# Spacing between room centres on the character grid.
	_COL_SPACING = 4
	_ROW_SPACING = 2

	def __init__(self, current_room: Room, visited_rooms: set[Room]) -> None:
		self._room = current_room
		self._visited = visited_rooms

	def build(self) -> Panel:
		"""Build the ASCII map panel showing all rooms in the area."""
		positions, edges = self._bfs_rooms()

		# Determine grid bounds and compute offset to centre the map.
		if not positions:
			return self._empty_panel()

		min_dx = min(dx for dx, _ in positions.values())
		max_dx = max(dx for dx, _ in positions.values())
		min_dy = min(dy for _, dy in positions.values())
		max_dy = max(dy for _, dy in positions.values())

		# Character-grid sized to fit the rooms exactly.
		g_cols = (max_dx - min_dx) * self._COL_SPACING + 1
		g_rows = (max_dy - min_dy) * self._ROW_SPACING + 1
		g = [[" "] * g_cols for _ in range(g_rows)]

		# Offset so that min_dx/min_dy maps to column/row 0.
		off_col = -min_dx * self._COL_SPACING
		off_row = -min_dy * self._ROW_SPACING

		# Draw connections first (so room symbols overwrite if overlapping).
		for edge in edges:
			p1, p2 = tuple(edge)
			self._draw_connection(g, p1, p2, off_col, off_row)

		# Draw room symbols.
		for room, (dx, dy) in positions.items():
			col = dx * self._COL_SPACING + off_col
			row = dy * self._ROW_SPACING + off_row
			if 0 <= row < len(g) and 0 <= col < len(g[0]):
				if room is self._room:
					g[row][col] = "[bold yellow]@[/bold yellow]"
				elif room in self._visited:
					g[row][col] = "[cyan]#[/cyan]"
				else:
					g[row][col] = "[dim]O[/dim]"

		out = "\n".join("".join(row) for row in g)
		return Panel(
			Text.from_markup(out),
			title="[bold]Map[/bold]",
			border_style="yellow",
			box=box.ROUNDED,
		)

	# ------------------------------------------------------------------
	# BFS discovery
	# ------------------------------------------------------------------

	def _bfs_rooms(self):
		"""Discover all rooms reachable from the current room.

		Returns:
			positions: dict mapping Room -> (dx, dy) logical coordinate.
			edges: set of frozenset pairs representing connections to draw.
		"""
		positions: dict[Room, tuple[int, int]] = {self._room: (0, 0)}
		occupied: dict[tuple[int, int], Room] = {(0, 0): self._room}
		edges: set[frozenset] = set()
		queue: deque[Room] = deque([self._room])
		seen: set[Room] = {self._room}

		while queue:
			room = queue.popleft()
			room_pos = positions[room]
			for d, neighbor in room.connected_rooms.items():
				dx, dy = DIR_VECTOR[d]
				npos = (room_pos[0] + dx, room_pos[1] + dy)

				if neighbor not in positions:
					if npos in occupied:
						continue
					positions[neighbor] = npos
					occupied[npos] = neighbor

				p2 = positions.get(neighbor)
				if p2 is not None:
					edges.add(frozenset((room_pos, p2)))

				if neighbor not in seen:
					seen.add(neighbor)
					queue.append(neighbor)

		return positions, edges

	# ------------------------------------------------------------------
	# Connection drawing
	# ------------------------------------------------------------------

	def _draw_connection(self, g, p1, p2, off_col, off_row):
		"""Draw a connector between two logically adjacent rooms."""
		ddx = p2[0] - p1[0]
		ddy = p2[1] - p1[1]
		if abs(ddx) > 1 or abs(ddy) > 1:
			return

		c1 = p1[0] * self._COL_SPACING + off_col
		r1 = p1[1] * self._ROW_SPACING + off_row

		def _put(r, c, ch):
			if 0 <= r < len(g) and 0 <= c < len(g[0]):
				g[r][c] = f"[dim]{ch}[/dim]"

		if ddx == 0 and ddy == -1:
			# North: vertical connector above
			_put(r1 - 1, c1, "|")
		elif ddx == 0 and ddy == 1:
			# South: vertical connector below
			_put(r1 + 1, c1, "|")
		elif ddx == 1 and ddy == 0:
			# East: horizontal connectors
			for i in range(1, self._COL_SPACING):
				_put(r1, c1 + i, "-")
		elif ddx == -1 and ddy == 0:
			# West: horizontal connectors
			for i in range(1, self._COL_SPACING):
				_put(r1, c1 - i, "-")
		elif ddx == 1 and ddy == -1:
			# North-east: diagonal
			_put(r1 - 1, c1 + 1, "/")
		elif ddx == -1 and ddy == -1:
			# North-west: diagonal
			_put(r1 - 1, c1 - 1, "\\")
		elif ddx == 1 and ddy == 1:
			# South-east: diagonal
			_put(r1 + 1, c1 + 1, "\\")
		elif ddx == -1 and ddy == 1:
			# South-west: diagonal
			_put(r1 + 1, c1 - 1, "/")

	# ------------------------------------------------------------------

	@staticmethod
	def _empty_panel() -> Panel:
		return Panel(
			Text("No map data."),
			title="[bold]Map[/bold]",
			border_style="yellow",
			box=box.ROUNDED,
		)
