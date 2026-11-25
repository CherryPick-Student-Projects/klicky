#!/usr/bin/env python3
"""Propose default-branch integration without merging or executing incoming code."""

import argparse
import json
import os
import subprocess
import sys
from urllib.parse import urlencode


REPOSITORIES = {
    "Muneer320/klicky": ("CherryPick-Student-Projects/klicky", "codex/sync-cherrypick"),
    "CherryPick-Student-Projects/klicky": ("Muneer320/klicky", "codex/sync-upstream"),
}
MARKER = "<!-- klicky-club-sync -->"


def command(*args):
    return subprocess.check_output(args, text=True, encoding="utf-8").strip()


def api(path, data=None):
    args = ["gh", "api", path]
    if data is None:
        return json.loads(command(*args))
    result = subprocess.run(
        [*args, "--method", "POST", "--input", "-"],
        input=json.dumps(data), text=True, encoding="utf-8", capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def ancestor(old, new):
    result = subprocess.run(["git", "merge-base", "--is-ancestor", old, new], check=False)
    if result.returncode not in (0, 1):
        raise RuntimeError("Cannot verify sync branch ancestry.")
    return result.returncode == 0


def sync(repository, dry_run=False):
    source, branch = REPOSITORIES[repository]
    owner = repository.split("/")[0]
    if command("git", "rev-parse", "--is-shallow-repository") == "true":
        raise RuntimeError("Full Git history is required; use checkout fetch-depth: 0.")
    # Explicit refspecs never fetch tags or modify a default branch. Incoming
    # files remain Git objects; no checkout, build or hooks from the source run.
    for name, remote in (("base", repository), ("source", source)):
        command("git", "fetch", "--no-tags", f"https://github.com/{remote}.git",
                f"+refs/heads/master:refs/klicky-sync/{name}")
    base = command("git", "rev-parse", "refs/klicky-sync/base")
    head = command("git", "rev-parse", "refs/klicky-sync/source")
    ahead = int(command("git", "rev-list", "--count", f"{base}..{head}"))
    incoming = ahead > 0 and command("git", "rev-parse", f"{base}^{{tree}}") != command(
        "git", "rev-parse", f"{head}^{{tree}}"
    )

    query = urlencode({"state": "all", "base": "master", "head": f"{owner}:{branch}",
                       "per_page": 100, "sort": "created", "direction": "desc"})
    pulls = api(f"repos/{repository}/pulls?{query}")
    opened = [pr for pr in pulls if pr["state"] == "open"]
    if len(opened) > 1 or any(MARKER not in (pr.get("body") or "") for pr in opened):
        raise RuntimeError("Reserved sync branch has an unexpected PR; inspect it manually.")
    if not incoming and not opened:
        print("No incoming file changes; no sync PR needed.")
        return
    if not opened and pulls and not pulls[0].get("merged_at") and pulls[0]["head"]["sha"] == head:
        print("This revision's sync PR was closed without merging; leaving it closed.")
        return

    remote_url = f"https://github.com/{repository}.git"
    ref = f"refs/heads/{branch}"
    existing = command("git", "ls-remote", "--heads", remote_url, ref)
    if existing:
        command("git", "fetch", "--no-tags", remote_url,
                f"+{ref}:refs/klicky-sync/previous")
        if not ancestor("refs/klicky-sync/previous", head):
            raise RuntimeError("Sync branch diverged or source history was rewritten. "
                               "Resolve manually; no force push was attempted.")

    print(f"Propose {source}@{head} -> {repository}:master ({ahead} incoming commits).")
    if dry_run:
        print("Dry run: no remote branch or PR changed.")
        return
    # Ordinary push rejects non-fast-forward races. Never push master, tags,
    # or force-update an existing branch.
    command("git", "-c", "core.hooksPath=/dev/null", "push", remote_url, f"{head}:{ref}")
    if opened:
        print(f"Existing sync PR refreshed: {opened[0]['html_url']}")
        return
    body = (
        f"{MARKER}\n"
        f"Bring default-branch changes from [{source}](https://github.com/{source}) "
        f"into `{repository}:master`.\n\n"
        "Review the diff, CI and the source PRs before merging. Use **Create a merge commit** "
        "to preserve shared history; do not squash or rebase this integration PR. "
        "Resolve conflicts on the source side or through a separately reviewed integration branch.\n\n"
        "This PR does not merge itself, close upstream issues, publish releases or deploy the site. "
        "Reference the original issues when their fixes are accepted upstream.\n\n"
        "[Shared contribution board](https://github.com/users/Muneer320/projects/1)"
    )
    pr = api(f"repos/{repository}/pulls", {
        "title": f"chore: sync changes from {source.split('/')[0]}",
        "head": branch, "base": "master", "body": body,
    })
    print(f"Created sync PR: {pr['html_url']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--repository", choices=REPOSITORIES,
                        default=os.environ.get("GITHUB_REPOSITORY", ""))
    args = parser.parse_args()
    repository = args.repository
    if repository not in REPOSITORIES:
        parser.error("Run only in one of the two configured Klicky repositories.")
    sync(repository, args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Sync stopped: {error}", file=sys.stderr)
        sys.exit(1)
