#!/usr/bin/env bash
# Daily headless run of the /ass-daily skill (see SKILL.md next to this file), then a gated push.
# Triggered by the claude-ass-daily systemd user timer; logs go to logs/ in the repo (gitignored).
set -euo pipefail

H="$HOME"
REPO="$H/alphacentauri-solar-sail"
SKILL_DIR="$REPO/.claude/skills/ass-daily"
cd "$REPO"
mkdir -p logs "$H/.cache/uv"
exec >> "logs/$(date +%F).log" 2>&1
echo "=== ass-daily run $(date -Is) ==="

# The agent commits everything it finds, so it must not sweep up a human's unfinished work.
if [ -n "$(git status --porcelain)" ]; then
  echo "ABORT: repository has uncommitted changes. Commit or stash, then rerun."
  exit 1
fi

export GIT_SSH_COMMAND="ssh -o BatchMode=yes"  # fail rather than wait for a passphrase
git fetch -q origin
git merge -q --ff-only origin/main  # picks up edits made on GitHub, aborts if history diverged

# The optional ADS token lives outside the sandbox.
ads_token=""
[ -r "$H/.config/ass/ads_token" ] && ads_token=$(< "$H/.config/ass/ads_token")
export ADS_API_TOKEN="$ads_token"

# Fetching the web and running code in one agent needs a boundary, and its commits get published.
# So $HOME is empty except for this repo, tools and the login. systemd's ProtectHome is silently
# ignored in user units on this machine, hence bwrap. Read-only paths stop a bad run from changing
# its own runner, git hooks, CI or MCP config.
sandbox=(
  bwrap --ro-bind / / --dev /dev --proc /proc --tmpfs /tmp --tmpfs "/run/user/$(id -u)"
  --tmpfs "$H"
  --bind "$REPO" "$REPO"
  --ro-bind "$REPO/.git/hooks" "$REPO/.git/hooks"
  --ro-bind "$REPO/.git/config" "$REPO/.git/config"
  --ro-bind "$REPO/.claude" "$REPO/.claude"
  --ro-bind "$REPO/.github" "$REPO/.github"
  --ro-bind "$REPO/.mcp.json" "$REPO/.mcp.json"
  --bind "$H/.cache/uv" "$H/.cache/uv"
  --ro-bind "$H/.local/share/uv" "$H/.local/share/uv"
  --ro-bind "$H/.local/bin" "$H/.local/bin"
  --ro-bind "$H/.local/share/claude" "$H/.local/share/claude"
  --bind "$H/.claude" "$H/.claude"
)
# The login must stay writable in a real directory so token refresh works. Everything else in
# ~/.claude (conversation history, memory, settings, plugins) is hidden: it holds private work.
for entry in "$H"/.claude/* "$H"/.claude/.[!.]*; do
  [ "$entry" = "$H/.claude/.credentials.json" ] && continue
  if [ -d "$entry" ]; then sandbox+=(--tmpfs "$entry"); else sandbox+=(--ro-bind /dev/null "$entry"); fi
done
sandbox+=(--die-with-parent)
export PATH="$H/.local/bin:$PATH"

ahead() { [ -n "$(git rev-list origin/main..HEAD)" ]; }

# A previous run's commit that failed to publish goes first, so a retry does not stack iterations.
if ! ahead; then
  # `opus` is an alias, so the project moves to each new Opus model by itself.
  "${sandbox[@]}" "$H/.local/bin/claude" -p "/ass-daily" \
    --model opus \
    --mcp-config .mcp.json --strict-mcp-config \
    --allowedTools "mcp__ass-research,Read,Write,Edit,Glob,Grep,ToolSearch,WebSearch,WebFetch,Bash(uv:*),Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git show:*),Bash(git add:*),Bash(git commit:*),Bash(git restore:*),Bash(git clean:*),Bash(mkdir:*),Bash(date:*),Bash(ls:*)"
fi

if ahead; then
  if [ -n "$(git status --porcelain)" ]; then
    echo "NOT PUBLISHED: the agent left uncommitted changes."
    exit 1
  fi
  # Agent-written code is only ever run inside the sandbox, never on the host.
  "${sandbox[@]}" "$H/.local/bin/uv" run --quiet ruff check .
  "${sandbox[@]}" "$H/.local/bin/uv" run --quiet pytest -q
  "$SKILL_DIR/scan_secrets.sh" origin/main..HEAD "$ads_token"
  git push -q origin main  # never forced
  echo "published $(git rev-parse --short HEAD)"
fi
echo "=== finished $(date -Is) ==="
