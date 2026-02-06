"""Re-stage any files modified by prior pre-commit hooks.

Should be the LAST hook in .pre-commit-config.yaml.
"""

import subprocess
import sys


def main():
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        capture_output=True, text=True,
    )
    modified = result.stdout.splitlines()
    if modified:
        subprocess.run(["git", "add"] + modified)
    sys.exit(0)


if __name__ == "__main__":
    main()
