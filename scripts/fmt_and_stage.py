"""Format staged Python files and re-stage changes.

Runs black and ruff --fix on staged .py files,
then re-stages them so the commit includes the fixes.
"""

import subprocess
import sys


def get_staged_py_files():
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only",
         "--diff-filter=ACM"],
        capture_output=True, text=True,
    )
    return [
        f for f in result.stdout.splitlines()
        if f.endswith(".py")
    ]


def main():
    files = get_staged_py_files()
    if not files:
        sys.exit(0)

    subprocess.run(
        ["black"] + files,
        capture_output=True,
    )
    subprocess.run(
        ["ruff", "check", "--fix"] + files,
        capture_output=True,
    )

    # - trim trailing whitespace
    # - ensure file ends with a single newline
    for path in files:
        try:
            with open(path, "rb+") as fh:
                data = fh.read()
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    # skip binary or non-utf8 files
                    continue

                # trim trailing whitespace on each line
                lines = [ln.rstrip() for ln in text.splitlines()]
                # ensure file ends with exactly one newline
                new_text = "\n".join(lines) + "\n"
                if new_text != text:
                    fh.seek(0)
                    fh.write(new_text.encode("utf-8"))
                    fh.truncate()
        except FileNotFoundError:
            # file may have been removed between staging and now
            continue

    subprocess.run(["git", "add"] + files)
    sys.exit(0)


if __name__ == "__main__":
    main()
