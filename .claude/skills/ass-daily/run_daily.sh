#!/usr/bin/env bash
# Daily headless run of the /ass-daily skill (see SKILL.md next to this file).
# Triggered by the claude-ass-daily systemd user timer; logs go to logs/ in the repo (gitignored).
set -euo pipefail

H="$HOME"
REPO="$H/alphacentauri-solar-sail"
cd "$REPO"
mkdir -p logs "$H/.cache/uv"
exec >> "logs/$(date +%F).log" 2>&1
echo "=== ass-daily run $(date -Is) ==="

# The agent commits everything it finds, so it must not sweep up a human's unfinished work.
if ! git rev-parse -q --verify HEAD > /dev/null || [ -n "$(git status --porcelain)" ]; then
  echo "ABORT: repository has no commits or has uncommitted changes. Commit or stash, then rerun."
  exit 1
fi

# Fetching the web and running code in one agent needs a boundary, so hide the rest of $HOME
# (SSH keys, work repos). systemd's ProtectHome is silently ignored in user units on this machine.
# Read-only paths stop a bad run from persisting outside this run via hooks or its own runner.
sandbox=(
  bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp --tmpfs "/run/user/$(id -u)"
  --tmpfs "$H"
  --bind "$REPO" "$REPO"
  --ro-bind "$REPO/.git/hooks" "$REPO/.git/hooks"
  --ro-bind "$REPO/.git/config" "$REPO/.git/config"
  --ro-bind "$REPO/.claude" "$REPO/.claude"
  --bind "$H/.claude" "$H/.claude"
  --ro-bind "$H/.claude/settings.json" "$H/.claude/settings.json"
  --ro-bind "$H/.claude/skills" "$H/.claude/skills"
  --ro-bind "$H/.claude/plugins" "$H/.claude/plugins"
  --bind "$H/.claude.json" "$H/.claude.json"
  --bind "$H/.cache/uv" "$H/.cache/uv"
  --ro-bind "$H/.local/share/uv" "$H/.local/share/uv"
  --ro-bind "$H/.local/bin" "$H/.local/bin"
  --ro-bind "$H/.local/share/claude" "$H/.local/share/claude"
  --ro-bind "$H/.gitconfig" "$H/.gitconfig"
  --die-with-parent
)

# `opus` is an alias, so the project moves to each new Opus model by itself.
status=0
PATH="$H/.local/bin:$PATH" "${sandbox[@]}" "$H/.local/bin/claude" -p "/ass-daily" \
  --model opus \
  --allowedTools "Read,Write,Edit,Glob,Grep,ToolSearch,WebSearch,WebFetch,Bash(uv:*),Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git show:*),Bash(git add:*),Bash(git commit:*),Bash(git restore:*),Bash(git clean:*),Bash(mkdir:*),Bash(date:*),Bash(ls:*)" \
  || status=$?
echo "=== finished $(date -Is), exit $status, HEAD $(git rev-parse --short HEAD) ==="
exit "$status"
