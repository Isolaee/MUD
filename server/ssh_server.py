"""
Example: Serving the MUD TUI over SSH.

Each connecting client gets their own session starting with
character creation, then transitioning to the full game UI —
all rendered server-side into the SSH pseudo-terminal.

Requirements:
    pip install asyncssh rich

Environment variables:
    SSH_HOST_KEY:  Contents of the RSA private key (PEM format).
                   If not set, falls back to server/host_key file.
    SSH_PORT:      Port to listen on (default: 8022).

Usage:
    1. Set env var:  export SSH_HOST_KEY="$(cat host_key)"
       Or generate:  ssh-keygen -t rsa -f host_key -N ""
    2. Run:          python ssh_server.py
    3. Connect:      ssh -p 8022 localhost
"""

import asyncio
import sys
import os
from io import StringIO

import asyncssh
from rich.console import Console

# Add project root to path so we can import game modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.database import init_db
from server.world_manager import WorldManager
from UI.login_ui import LoginUI


# -- Refresh rate for the render loop --
FPS = 20

# Module-level world manager, created during start_server().
_world: WorldManager | None = None


class SSHGameSession:
	"""A single player's game session over SSH.

	Owns a View (starting with LoginUI) and drives the render loop
	+ input handling that normally lives in Application and
	InputHandler, but adapted for async SSH I/O.
	"""

	def __init__(self, process: asyncssh.SSHServerProcess, world: WorldManager):
		self.process = process
		self.world = world
		self.view = LoginUI(world)
		self.active_character_id: int | None = None

	def _get_active_view(self):
		"""Walk the next_view chain to find the leaf view."""
		v = self.view
		while v.next_view is not None:
			v = v.next_view
		return v

	def _render_frame(self, width: int, height: int) -> str:
		"""Render the current view's layout to a string via Rich.

		Uses the same render pipeline as Live(screen=True):
		explicitly set ConsoleOptions.height so Layout fills the
		entire terminal area.
		"""
		console = Console(
			file=StringIO(),
			width=width,
			height=height,
			force_terminal=True,
			color_system="256",
		)

		layout = self.view.build_layout()

		# Build ConsoleOptions with the exact terminal height.
		# This is what Live(screen=True) does internally — without it,
		# Layout collapses to minimum content height.
		options = console.options.update_height(height)
		segments = console.render(layout, options)
		lines = console._render_buffer(segments)
		return lines

	async def run(self):
		"""Main session loop: render frames and read input concurrently."""
		proc = self.process

		term_size = proc.get_terminal_size()
		width = term_size[0] if term_size else 80
		height = term_size[1] if term_size else 24

		# Put terminal in raw mode: hide cursor, switch to alternate
		# screen buffer, and suppress local echo via stty-style modes.
		proc.channel.set_line_mode(False)
		proc.channel.set_echo(False)
		proc.stdout.write("\033[?1049h")  # alternate screen buffer
		proc.stdout.write("\033[?25l")  # hide cursor

		input_task = asyncio.create_task(self._input_loop(proc))
		render_task = asyncio.create_task(self._render_loop(proc, width, height))

		try:
			done, pending = await asyncio.wait(
				[input_task, render_task],
				return_when=asyncio.FIRST_COMPLETED,
			)
			for task in pending:
				task.cancel()
		except asyncio.CancelledError:
			pass
		finally:
			# Clean up player from shared world on disconnect
			if self.active_character_id is not None:
				self.world.leave(self.active_character_id)
			proc.stdout.write("\033[?25h")  # show cursor
			proc.stdout.write("\033[?1049l")  # restore main screen buffer
			proc.stdout.write("Thanks for playing! Goodbye.\r\n")
			proc.exit(0)

	async def _render_loop(self, proc, width: int, height: int):
		"""Redraw the screen at a fixed frame rate."""
		interval = 1 / FPS
		last_frame = ""
		while self.view.running:
			# Check for terminal resize
			term_size = proc.get_terminal_size()
			if term_size:
				width, height = term_size[0], term_size[1]

			# Track active character_id for disconnect cleanup
			active = self._get_active_view()
			char_id = getattr(active, "character_id", None)
			if char_id is not None:
				self.active_character_id = char_id

			frame = self._render_frame(width, height)

			# Only redraw if the frame changed (reduces flicker)
			if frame != last_frame:
				# Move cursor to top-left instead of clearing (less flicker)
				proc.stdout.write("\033[H")
				proc.stdout.write(frame)
				last_frame = frame

			await asyncio.sleep(interval)

	async def _input_loop(self, proc):
		"""Read keystrokes one character at a time from the SSH session."""
		while self.view.running:
			try:
				data = await proc.stdin.read(1)
			except (asyncssh.BreakReceived, asyncssh.TerminalSizeChanged):
				continue
			except asyncssh.DisconnectError:
				self.view.running = False
				break

			if not data or proc.stdin.at_eof():
				self.view.running = False
				break

			char = data

			if char == "\r" or char == "\n":
				active = self._get_active_view()
				self.view.handle_input(active.input_buffer)
				active = self._get_active_view()
				active.input_buffer = ""

			elif char == "\x7f" or char == "\x08":
				active = self._get_active_view()
				active.input_buffer = active.input_buffer[:-1]

			elif char == "\t":
				active = self._get_active_view()
				active.handle_tab()

			elif char == "\x03":
				self.view.running = False
				break

			elif char == "\x1b":
				# Escape sequence (arrow keys etc.) — consume remaining bytes
				try:
					next_char = await asyncio.wait_for(proc.stdin.read(1), timeout=0.05)
					if next_char == "[":
						await asyncio.wait_for(proc.stdin.read(1), timeout=0.05)
				except (asyncio.TimeoutError, asyncssh.BreakReceived):
					pass

			elif char.isprintable():
				active = self._get_active_view()
				active.input_buffer += char


class MudSSHServer(asyncssh.SSHServer):
	"""SSH server that accepts connections and spawns game sessions."""

	def connection_made(self, conn):
		peername = conn.get_extra_info("peername")
		addr = peername[0] if peername else "unknown"
		print(f"[+] Connection from {addr}")

	def connection_lost(self, exc):
		print("[-] Connection closed.")

	def begin_auth(self, username):
		return False

	def password_auth_supported(self):
		return True

	def validate_password(self, username, password):
		return True


async def handle_client(process: asyncssh.SSHServerProcess):
	"""Called when a client opens a shell session."""
	session = SSHGameSession(process, _world)
	await session.run()


def _load_host_key():
	"""Load the SSH host key from env var or fall back to file.

	Returns an asyncssh private key object.
	"""
	key_data = os.environ.get("SSH_HOST_KEY")
	if key_data:
		return asyncssh.import_private_key(key_data)

	# Fall back to key file next to this script
	key_path = os.path.join(os.path.dirname(__file__), "host_key")
	if os.path.exists(key_path):
		return asyncssh.read_private_key(key_path)

	print("ERROR: No SSH host key found.")
	print("Either set the SSH_HOST_KEY environment variable,")
	print('or generate a key file:  ssh-keygen -t rsa -f server/host_key -N ""')
	return None


async def start_server():
	"""Start the SSH server."""
	global _world

	# Initialise database and shared world state
	init_db()
	_world = WorldManager()
	_world.load_world()
	print("World loaded.")

	host_key = _load_host_key()
	if host_key is None:
		return

	port = int(os.environ.get("SSH_PORT", "8022"))

	await asyncssh.create_server(
		MudSSHServer,
		"",
		port,
		server_host_keys=[host_key],
		process_factory=handle_client,
	)

	print(f"MUD SSH server running on port {port}")
	print(f"Connect with:  ssh -p {port} localhost")
	await asyncio.Future()


if __name__ == "__main__":
	asyncio.run(start_server())
