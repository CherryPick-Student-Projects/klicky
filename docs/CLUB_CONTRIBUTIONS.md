# CherryPick contributions

[Muneer320/klicky](https://github.com/Muneer320/klicky) is the canonical repository
for Klicky, releases and the website. The
[CherryPick fork](https://github.com/CherryPick-Student-Projects/klicky) is the
contribution entry point for the college club. Students open PRs there so the
club can track their work. Both use `master` as their default branch.

## Find and link work

Use the [shared contribution board](https://github.com/users/Muneer320/projects/1)
to find issues and PRs across both repositories. Board entries point to the real
GitHub items; comments, reviews and authorship remain in their source repositories.

Before starting, search both repositories and agree on the scope. If an issue
already exists upstream, create a focused club issue only when needed for club
tracking. Include `Related to https://github.com/Muneer320/klicky/issues/NUMBER`,
and add the club issue's URL to the original issue. Link both from the club PR.
Use the new issue forms' optional **Related issue** field for these links.

A club PR can close its club issue. Reference the upstream issue with **Related
to**, rather than a closing keyword, until the fix is actually accepted upstream.
The upstream integration PR can then close the original issue after its complete
acceptance criteria pass. A merge into the fork alone does not resolve an
upstream issue or make a feature available in a release.

Keep discussions on the original item instead of copying every comment or review.
For work available in both repositories, check the linked issue before assigning
someone else to avoid two people independently implementing the same change.

## How code reaches both repositories

1. Create a feature branch and open a PR against the club fork.
2. Review it and pass the relevant checks. All merges remain manual.
3. The original repository's sync workflow notices incoming club commits and
   opens or refreshes one integration PR from `codex/sync-cherrypick` to `master`.
4. Review that PR and use **Create a merge commit**. Do not squash or rebase an
   integration PR: the repositories need shared commit ancestry.
5. The same workflow proposes incoming upstream changes to the fork through
   `codex/sync-upstream`. Review and merge that PR with a merge commit too.

Feature PRs can still use the normal squash-merge convention. The merge-commit
requirement applies to repository integration PRs, preserving feature authors and
their commits without repeatedly proposing changes that were already integrated.

The workflow runs only in the original repository, checking both directions on
pushes to `master`, roughly every six hours, and on manual dispatch. The schedule
is best effort; GitHub may delay it. Incoming changes are
fetched as Git objects and never checked out or executed by the sync job. Only
the two configured repositories and their `master` branches are eligible. The
job writes a reserved sync branch in its destination repository, opens a PR, and never
merges, pushes default branches, force-pushes, copies tags or publishes anything.

Equal file trees produce no new PR, even when merge commits differ. An existing
sync PR is still refreshed if the source reverts its changes, so it cannot retain
an obsolete patch. Repeated checks refresh the same open PR. Closing a sync PR without merging suppresses another
proposal for the same source revision; later source revisions can be proposed.
If the sync branch diverges or source history is rewritten, the workflow stops
without overwriting either history. Resolve conflicts through a reviewed change;
do not force-push a default branch or squash an integration PR to hide conflicts.
Do not use the reserved sync branches for unrelated work.

## Automation setup

Review and merge the setup PR in **both** repositories using merge commits.
Before activation, confirm that both default branches require PRs and passing CI,
and that merge commits are allowed. Keep the default Actions token read-only and
the Actions setting for creating/approving PRs unchanged. The automation uses a
dedicated GitHub App instead: the built-in token cannot push workflow-file
changes and would eventually stall repository sync.

Install the dedicated sync App on **only** `Muneer320/klicky` and
`CherryPick-Student-Projects/klicky`, with repository **Contents**, **Pull requests**
and **Workflows** set to read/write, plus mandatory Metadata read access. Grant no
organization, administration, secrets, member, issue or project permissions. The
club organization administrator may need to approve its installation. Do not add
the App to branch-protection bypass lists or give it release credentials. Its
Contents permission also permits release API writes; the reviewed workflow never
uses those APIs, so protect its key and review workflow edits carefully.

Store the App's client ID as the `CLUB_SYNC_CLIENT_ID` Actions variable and its
private key as the `CLUB_SYNC_PRIVATE_KEY` Actions secret **only in the original
repository**. No secret belongs in the fork or a source file. Each matrix job
mints a short-lived token restricted to its destination's single `klicky`
repository; the official token action revokes it after the job. It never approves
or merges PRs. Missing App configuration fails explicitly. The protected default
branch is the only source of executable sync code; proposed changes remain Git
objects until separately reviewed.

Enable normal CI in the fork, retaining contributor-run approvals.
The release-candidate, Store-package and APT/Pages workflows are restricted to
`Muneer320/klicky`. Do not copy release credentials into the fork or enable a
second production Pages site. Ordinary CI can build test artifacts in either repo.
Review workflow changes before merging; these guards do not replace GitHub
repository permissions or protect against an administrator changing the workflow.

Configure the shared board's native **Auto-add to project** workflows for each
repository, with `is:issue,pr is:open`. These add new or updated items by reference,
without copying text or changing issue or PR state. GitHub keeps the linked items'
titles and states current afterward. Backfill existing open items separately;
auto-add only reacts to future creation or updates. Keep automatic issue closure
disabled. This uses GitHub's native automation and needs no project token or
cross-repository credential. The number of auto-add workflows depends on the
account plan; this setup needs two.

After activation, run **Propose repository sync** manually in the original repository.
An identical pair should report no incoming file changes. The next reviewed
contribution should open one upstream integration PR; repeated runs must not
create duplicates. Verify CI actually runs on bot-created PRs and approve pending
runs through GitHub when required. Do not merge an unchecked PR.
