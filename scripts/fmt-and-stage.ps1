# Format Python files and auto-stage changes
# Used by pre-commit hook to automatically add formatted files

$stagedFiles = git diff --cached --name-only --diff-filter=ACM | Where-Object { $_ -match '\.py$' }

if ($stagedFiles) {
    # Run black formatter
    black $stagedFiles 2>$null

    # Run ruff with --fix for auto-fixable issues
    ruff check --fix $stagedFiles 2>$null

    # Re-stage the formatted files
    git add $stagedFiles
}

exit 0
