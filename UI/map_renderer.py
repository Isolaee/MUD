"""BFS map traversal and ASCII map rendering."""

from __future__ import annotations

from collections import deque

from rich import box
from rich.panel import Panel
from rich.text import Text

from Objects.room import Room, DIR_VECTOR


def _bfs_rooms(current_room: Room, max_depth: int = 2):
	positions = {current_room: (0, 0)}
	occupied = {(0, 0): current_room}
	edges = set()
	queue = deque([(current_room, 0)])
	visited = {current_room}

	while queue:
		room, depth = queue.popleft()
		room_pos = positions[room]
		if depth >= max_depth:
			continue
		for d, neighbor in room.connected_rooms.items():
			dx, dy = DIR_VECTOR[d]
			npos = (
				room_pos[0] + dx,
				room_pos[1] + dy,
			)
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
				edge = frozenset((p1, p2))
				edges.add(edge)
			if neighbor not in visited:
				visited.add(neighbor)
				queue.append((neighbor, depth + 1))

	return positions, edges


def _grid_pos(dx, dy):
	col = (dx + 2) * 6
	row = (dy + 2) * 4
	return col, row


def _place_box(g, col, row, label, style):
	s, e = f"[{style}]", f"[/{style}]"
	g[row][col] = f"{s}+--+{e}"
	g[row + 1][col] = f"{s}|{e}{label[:2]}{s}|{e}"
	g[row + 2][col] = f"{s}+--+{e}"
	for r in range(row, row + 3):
		for c in range(col + 1, col + 4):
			if c < len(g[0]):
				g[r][c] = ""


def _draw_path(g, p1, p2):
	ddx = p2[0] - p1[0]
	ddy = p2[1] - p1[1]
	if abs(ddx) > 1 or abs(ddy) > 1:
		return
	c1, r1 = _grid_pos(*p1)
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


def make_map(current_room: Room) -> Panel:
	positions, edges = _bfs_rooms(current_room, 2)
	GW = 30
	GH = 19
	g = [[" "] * GW for _ in range(GH)]

	for room, (dx, dy) in positions.items():
		col, row = _grid_pos(dx, dy)
		if room == current_room:
			_place_box(g, col, row, "@@", "bold yellow")
		else:
			_place_box(g, col, row, room.name, "cyan")

	for edge in edges:
		p1, p2 = tuple(edge)
		_draw_path(g, p1, p2)

	out = "\n".join("".join(row) for row in g)
	return Panel(
		Text.from_markup(out),
		title="[bold]Map[/bold]",
		border_style="yellow",
		box=box.ROUNDED,
	)
