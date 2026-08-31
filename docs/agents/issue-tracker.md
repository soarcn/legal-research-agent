# Issue tracker: GitHub

Issues and specs for this repository live as GitHub Issues. Use the `gh` CLI for all operations. The repository is inferred from the configured `origin` remote.

## Conventions

- Create: `gh issue create --title "..." --body "..."`
- Read: `gh issue view <number> --comments`
- List: `gh issue list --state open --json number,title,body,labels,comments`
- Comment: `gh issue comment <number> --body "..."`
- Add label: `gh issue edit <number> --add-label "..."`
- Remove label: `gh issue edit <number> --remove-label "..."`
- Close: `gh issue close <number> --comment "..."`

## Pull requests as a triage surface

**PRs as a request surface: no.**

## Skill operations

When a skill says “publish to the issue tracker”, create a GitHub Issue.

When a skill says “fetch the relevant ticket”, run:

`gh issue view <number> --comments`

## Dependencies

Use GitHub native issue dependencies where available. If unavailable, add a `Blocked by: #<number>` line to the issue body.

A ticket is ready only when all blocking issues are closed. Claim work with:

`gh issue edit <number> --add-assignee @me`
