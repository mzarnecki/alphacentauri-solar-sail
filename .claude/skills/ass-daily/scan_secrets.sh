#!/usr/bin/env bash
# Usage: scan_secrets.sh <git range> [literal secret ...]
# Exits 1 if the range's messages or diffs contain a credential. This gate stands between an agent
# that can read a login token and a public repository, so it fails closed on any git error.
set -euo pipefail

range="$1"
shift
patch=$(git log -p --text --no-ext-diff --no-textconv "$range")

pattern='sk-ant-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----'
if grep -qE -- "$pattern" <<< "$patch"; then
  echo "SECRET SCAN FAILED: credential-like text in $range" >&2
  exit 1
fi
for secret in "$@"; do
  if [ -n "$secret" ] && grep -qF -- "$secret" <<< "$patch"; then
    echo "SECRET SCAN FAILED: a known secret appears in $range" >&2
    exit 1
  fi
done
