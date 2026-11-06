"""Runs the real daily runner in a throwaway $HOME, with the agent, sandbox and GitHub stubbed."""

import os
import shutil
import stat
import subprocess
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
BRANCH = f"iteration/{date.today():%F}"
TEMPLATE = "## Human review\n"


def write_script(path, body):
    path.write_text(f"#!/usr/bin/env bash\n{body}\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


class Rig:
    def __init__(self, home):
        self.home = home
        self.repo = home / "alphacentauri-solar-sail"
        self.origin = home / "origin.git"
        self.bin = home / ".local/bin"
        self.calls = home / "calls.log"
        self.bin.mkdir(parents=True)
        (home / ".claude").mkdir()
        (home / ".claude/.credentials.json").write_text("{}")

        self.git_at(home, "init", "-q", "--bare", "-b", "main", str(self.origin))
        self.git_at(home, "init", "-q", "-b", "main", str(self.repo))
        skill = self.repo / ".claude/skills/ass-daily"
        skill.mkdir(parents=True)
        for name in ("run_daily.sh", "scan_secrets.sh"):
            shutil.copy(ROOT / ".claude/skills/ass-daily" / name, skill)
        (self.repo / ".github").mkdir()
        (self.repo / ".github/pull_request_template.md").write_text(TEMPLATE)
        (self.repo / ".mcp.json").write_text("{}")
        (self.repo / ".gitignore").write_text("logs/\n")
        self.git("remote", "add", "origin", str(self.origin))
        self.git("config", "user.name", "t")
        self.git("config", "user.email", "t@t")
        self.git("add", "-A")
        self.git("commit", "-qm", "base")
        self.git("push", "-q", "origin", "main")

        # Drops the sandbox flags and runs the command directly.
        write_script(
            self.bin / "bwrap",
            'while [ "$1" != "--die-with-parent" ]; do shift; done; shift; exec "$@"',
        )
        self.agent('git commit -q --allow-empty -m "iteration: add a thing"')
        self.tests_pass(True)
        # Answers "no PR yet" to the lookup and a URL to the creation, and records both.
        write_script(
            self.bin / "curl",
            f'echo "curl $*" >> {self.calls}\n'
            'case "$*" in *POST*) echo \'{"html_url": "https://example.test/pr/1"}\';;'
            " *) echo '[]';; esac",
        )

    def git_at(self, cwd, *args):
        return subprocess.run(
            ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
        ).stdout.strip()

    def git(self, *args):
        return self.git_at(self.repo, *args)

    def agent(self, body):
        write_script(self.bin / "claude", f'echo claude >> {self.calls}\n{body}')

    def tests_pass(self, passing):
        write_script(self.bin / "uv", "exit 0" if passing else "exit 1")

    def token(self):
        (self.home / ".config/ass").mkdir(parents=True)
        (self.home / ".config/ass/github_token").write_text("test-token")

    def run(self):
        env = {**os.environ, "HOME": str(self.home)}
        script = self.repo / ".claude/skills/ass-daily/run_daily.sh"
        return subprocess.run([script], env=env, check=False, capture_output=True).returncode

    def remote_branches(self):
        output = self.git_at(self.origin, "for-each-ref", "--format=%(refname:short)", "refs/heads")
        return set(output.split())

    def called(self):
        return self.calls.read_text() if self.calls.exists() else ""

    def log(self):
        return (self.repo / "logs" / f"{date.today():%F}.log").read_text()


@pytest.fixture
def rig(tmp_path):
    return Rig(tmp_path)


def test_agent_work_goes_to_a_branch_and_a_pr_never_to_main(rig):
    rig.token()
    main_before = rig.git("rev-parse", "origin/main")
    assert rig.run() == 0
    assert rig.remote_branches() == {"main", BRANCH}
    assert rig.git_at(rig.origin, "rev-parse", "main") == main_before
    assert "POST" in rig.called()
    assert "https://example.test/pr/1" in rig.log()
    assert rig.git("branch", "--show-current") == "main"
    assert rig.git("for-each-ref", "refs/heads/iteration/*") == ""


def test_token_never_reaches_the_process_arguments(rig):
    rig.token()
    rig.run()
    assert "test-token" not in rig.called()


def test_without_a_token_the_branch_is_pushed_and_a_link_is_logged(rig):
    assert rig.run() == 0
    assert BRANCH in rig.remote_branches()
    assert f"compare/main...{BRANCH}" in rig.log()
    assert "curl" not in rig.called()


def test_agent_does_not_run_while_a_pr_awaits_review(rig):
    rig.run()
    rig.calls.unlink()
    assert rig.run() == 0
    assert "claude" not in rig.called()
    assert "WAITING FOR REVIEW" in rig.log()


def test_agent_runs_again_after_the_pr_is_merged_and_its_branch_deleted(rig):
    rig.run()
    rig.git_at(rig.origin, "update-ref", "refs/heads/main", f"refs/heads/{BRANCH}")
    rig.git_at(rig.origin, "update-ref", "-d", f"refs/heads/{BRANCH}")
    rig.calls.unlink()
    assert rig.run() == 0
    assert "claude" in rig.called()
    assert rig.git("rev-parse", "main") == rig.git_at(rig.origin, "rev-parse", "main")


def test_failing_tests_publish_nothing_and_retry_does_not_rerun_the_agent(rig):
    rig.tests_pass(False)
    assert rig.run() != 0
    assert rig.remote_branches() == {"main"}
    rig.calls.unlink()
    rig.tests_pass(True)
    assert rig.run() == 0
    assert "claude" not in rig.called()
    assert BRANCH in rig.remote_branches()


def test_a_secret_publishes_nothing(rig):
    secret = "sk-" + "ant-" + "a" * 40
    rig.agent(f'echo "{secret}" > leak; git add leak; git commit -qm "iteration: oops"')
    assert rig.run() != 0
    assert rig.remote_branches() == {"main"}


def test_the_github_token_counts_as_a_secret(rig):
    rig.token()
    rig.agent('echo "test-token" > leak; git add leak; git commit -qm "iteration: oops"')
    assert rig.run() != 0
    assert rig.remote_branches() == {"main"}


def test_uncommitted_agent_work_publishes_nothing(rig):
    rig.agent('git commit -q --allow-empty -m "iteration: x"; echo x > stray')
    assert rig.run() != 0
    assert rig.remote_branches() == {"main"}
    assert "uncommitted" in rig.log()


def test_a_day_without_a_commit_leaves_no_branch(rig):
    rig.agent("true")
    assert rig.run() == 0
    assert rig.remote_branches() == {"main"}
    assert rig.git("branch", "--show-current") == "main"
    assert rig.git("for-each-ref", "refs/heads/iteration/*") == ""


def test_a_humans_uncommitted_work_stops_the_run_untouched(rig):
    (rig.repo / "wip").write_text("mine")
    assert rig.run() != 0
    assert "claude" not in rig.called()
    assert (rig.repo / "wip").read_text() == "mine"
