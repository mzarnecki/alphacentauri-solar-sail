#!/usr/bin/env bash
# Daily headless run of the /ass-daily skill (see SKILL.md next to this file). The agent works on an
# iteration/* branch, and the runner pushes it and opens a PR. Only a human merges into main.
# Triggered by the claude-ass-daily systemd user timer; logs go to logs/ in the repo (gitignored).
set -euo pipefail

H="$HOME"
REPO="$H/alphacentauri-solar-sail"
GITHUB_REPO="mzarnecki/alphacentauri-solar-sail"
SKILL_DIR="$REPO/.claude/skills/ass-daily"
cd "$REPO"
mkdir -p logs "$H/.cache/uv"
exec >> "logs/$(date +%F).log" 2>&1
echo "=== ass-daily run $(date -Is) ==="

# Runs switch branches and the agent commits everything, so never touch a human's unfinished work.
if [ -n "$(git status --porcelain)" ]; then
  echo "ABORT: repository has uncommitted changes. Commit or stash, then rerun."
  exit 1
fi

export GIT_SSH_COMMAND="ssh -o BatchMode=yes"  # fail rather than wait for a passphrase
git fetch -q --prune origin

# Both tokens stay outside the sandbox. The agent only ever gets the read-only ADS one.
ads_token=""
github_token=""
[ -r "$H/.config/ass/ads_token" ] && ads_token=$(< "$H/.config/ass/ads_token")
[ -r "$H/.config/ass/github_token" ] && github_token=$(< "$H/.config/ass/github_token")
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

github() {  # token goes through a config stream so it never appears in the process list
  curl --silent --show-error --fail-with-body --max-time 30 \
    --config <(printf 'header = "Authorization: Bearer %s"\n' "$github_token") \
    -H "Accept: application/vnd.github+json" "$@"
}

open_pr() {
  local branch="$1"
  if [ -z "$github_token" ]; then
    echo "NO PR: ~/.config/ass/github_token is missing. Open one by hand:"
    echo "https://github.com/$GITHUB_REPO/compare/main...$branch?expand=1"
    return
  fi
  local owner="${GITHUB_REPO%%/*}" count
  # python3 -I everywhere: never import agent-written files from this directory on the host.
  count=$(github "https://api.github.com/repos/$GITHUB_REPO/pulls?state=all&head=$owner:$branch" \
    | python3 -I -c 'import json, sys; print(len(json.load(sys.stdin)))')
  if [ "$count" != "0" ]; then
    return
  fi
  # The checklist comes from main, so a branch cannot weaken its own review.
  git show origin/main:.github/pull_request_template.md > /dev/null
  local payload
  payload=$(python3 -I -c '
import json, sys
branch, log, template = sys.argv[1:4]
title = log.splitlines()[0]
footer = "\U0001F916 Generated with [Claude Code](https://claude.com/claude-code)"
body = "\n\n".join(["## What changed", log.strip(), template.strip(), footer])
print(json.dumps({"title": title, "head": branch, "base": "main", "body": body}))
' "$branch" "$(git log --format=%B "origin/main..origin/$branch")" \
    "$(git show origin/main:.github/pull_request_template.md)")
  github -X POST "https://api.github.com/repos/$GITHUB_REPO/pulls" -d "$payload" \
    | python3 -I -c 'import json, sys; print(json.load(sys.stdin)["html_url"])'
}

publish() {
  local branch="$1"
  git switch -q "$branch"
  if [ -n "$(git status --porcelain)" ]; then
    echo "NOT PUBLISHED: the agent left uncommitted changes."
    exit 1
  fi
  # Agent-written code is only ever run inside the sandbox, never on the host.
  "${sandbox[@]}" "$H/.local/bin/uv" run --quiet ruff check .
  "${sandbox[@]}" "$H/.local/bin/uv" run --quiet pytest -q
  "$SKILL_DIR/scan_secrets.sh" "origin/main..$branch" "$ads_token" "$github_token"
  git push -q origin "$branch:refs/heads/$branch"  # never forced, never main
  git switch -q main
  git branch -q -D "$branch"  # from here on, a local iteration branch means "not yet published"
  echo "published $branch"
  open_pr "$branch"
}

git switch -q main
git merge -q --ff-only origin/main  # picks up merged PRs, aborts if history diverged

has_commits() { [ -n "$(git rev-list "origin/main..$1")" ]; }

# A previous attempt that failed the gate or the push goes first, so retries do not stack iterations.
unpublished=$(git for-each-ref --format='%(refname:short)' 'refs/heads/iteration/*' | head -1)
if [ -n "$unpublished" ]; then
  if has_commits "$unpublished"; then
    publish "$unpublished"
    echo "=== finished $(date -Is) ==="
    exit 0
  fi
  git branch -q -D "$unpublished"
fi

# One iteration awaits review at a time: unreviewed work must not become the base for more work.
# Merging or closing the PR has to delete the branch, which is what lets the agent run again.
waiting=$(git for-each-ref --format='%(refname:lstrip=3)' 'refs/remotes/origin/iteration/*' | head -1)
if [ -n "$waiting" ]; then
  echo "WAITING FOR REVIEW: $waiting is not merged yet, so the agent does not run today."
  open_pr "$waiting"  # covers a PR that could not be opened last time
  echo "=== finished $(date -Is) ==="
  exit 0
fi

branch="iteration/$(date +%F)"
git switch -q --no-track -c "$branch" origin/main

# `opus` is an alias, so the project moves to each new Opus model by itself.
"${sandbox[@]}" "$H/.local/bin/claude" -p "/ass-daily" \
  --model opus \
  --mcp-config .mcp.json --strict-mcp-config \
  --allowedTools "mcp__ass-research,Read,Write,Edit,Glob,Grep,ToolSearch,WebSearch,WebFetch,Bash(uv:*),Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git show:*),Bash(git add:*),Bash(git commit:*),Bash(git restore:*),Bash(git clean:*),Bash(mkdir:*),Bash(date:*),Bash(ls:*)"

if has_commits "$branch"; then
  publish "$branch"
else
  echo "NOT PUBLISHED: the agent made no commit."
  git switch -q main
  git branch -q -D "$branch"
fi
echo "=== finished $(date -Is) ==="
