# Re-stage any files modified by prior pre-commit hooks
# This should be the LAST hook in .pre-commit-config.yaml

$modified = git diff --name-only
if ($modified) {
    git add $modified
}

exit 0
