import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / ".claude/skills/ass-daily/scan_secrets.sh"


@pytest.fixture
def repo(tmp_path):
    def git(*args):
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=tmp_path, check=True, capture_output=True,
        )

    (tmp_path / "base").write_text("base\n")
    git("init", "-q", "-b", "main")
    git("add", "-A")
    git("commit", "-qm", "base")

    def commit(text, message="change"):
        (tmp_path / "f").write_text(text)
        git("add", "-A")
        git("commit", "-qm", message)

    commit.path = tmp_path
    return commit


def scan(repo, *extra, range_="HEAD~1..HEAD"):
    return subprocess.run(
        [SCRIPT, range_, *extra], check=False, cwd=repo.path, capture_output=True, text=True
    ).returncode


def test_clean_commit_passes(repo):
    repo("a harmless sail\n")
    assert scan(repo) == 0


# Assembled at runtime so this test file does not trip the scanner itself.
@pytest.mark.parametrize(
    "secret",
    [
        "sk-" + "ant-" + "a" * 40,
        "ghp" + "_" + "a" * 36,
        "github" + "_pat_" + "a" * 30,
        "AK" + "IA" + "A" * 16,
        "-----BEGIN RSA " + "PRIVATE KEY-----",
    ],
)
def test_credentials_in_a_diff_are_blocked(repo, secret):
    repo(f"token = {secret}\n")
    assert scan(repo) == 1


def test_credentials_in_a_commit_message_are_blocked(repo):
    repo("fine\n", message="oops " + "sk-" + "ant-" + "a" * 40)
    assert scan(repo) == 1


def test_known_secret_is_blocked_and_empty_one_is_ignored(repo):
    repo("value: plain-looking-token\n")
    assert scan(repo, "plain-looking-token") == 1
    assert scan(repo, "") == 0


def test_bad_range_fails_closed(repo):
    repo("fine\n")
    assert scan(repo, range_="no-such-ref..HEAD") != 0
