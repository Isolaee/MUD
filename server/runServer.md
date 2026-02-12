# Running the MUD SSH Server

## Prerequisites

- Python 3.10+
- Dependencies installed: `pip install -r requirements.txt`

## Step 1: Generate an SSH Host Key

The server needs an RSA key pair to identify itself to connecting clients.
Run this once from the project root:

```bash
ssh-keygen -t rsa -f server/host_key -N ""
```

This creates two files in `server/`:
- `host_key` - private key (secret, never commit this)
- `host_key.pub` - public key

Both are already in `.gitignore`.

## Step 2: Start the Server

### Option A: Using the key file (local development)

```bash
python server/ssh_server.py
```

The server finds `server/host_key` automatically.

### Option B: Using environment variables (production / CI)

```bash
export SSH_HOST_KEY="$(cat server/host_key)"
export SSH_PORT=8022
python server/ssh_server.py
```

| Variable       | Description                          | Default |
|----------------|--------------------------------------|---------|
| `SSH_HOST_KEY` | RSA private key contents (PEM)       | None    |
| `SSH_PORT`     | Port the server listens on           | 8022    |

## Step 3: Connect

From any terminal with an SSH client:

```bash
ssh -p 8022 localhost
```

- Accept the host key fingerprint on first connection.
- Enter any username and password (authentication is not enforced yet).
- You will enter **character creation** (name, class, confirm).
- After confirming, the full game UI loads.

### Connecting from another machine

Replace `localhost` with the server's IP address:

```bash
ssh -p 8022 192.168.1.100
```

Make sure port 8022 is open in the firewall.

## Controls

| Key         | Action                     |
|-------------|----------------------------|
| Type + Enter| Submit command             |
| Tab         | Auto-complete              |
| Backspace   | Delete last character      |
| Ctrl+C      | Quit                       |

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.
