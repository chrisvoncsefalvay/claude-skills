# GitHub CLI and Projects Reference

This reference provides essential information about using the gh CLI with GitHub Projects.

## Authentication

Check authentication status:
```bash
gh auth status
```

Login if needed:
```bash
gh auth login
```

## Repository Detection

Get remote URL:
```bash
git remote get-url origin
```

List all remotes:
```bash
git remote -v
```

## GitHub Projects Commands

### List Projects

For an organisation or user:
```bash
gh project list --owner OWNER [--format json]
```

Example output (JSON):
```json
{
  "projects": [
    {
      "number": 1,
      "title": "Sprint Planning",
      "url": "https://github.com/orgs/example/projects/1"
    }
  ]
}
```

### View Project

```bash
gh project view NUMBER --owner OWNER
```

### Add Item to Project

```bash
gh project item-add PROJECT_NUMBER --owner OWNER --url ISSUE_URL
```

The `--url` must be a full GitHub URL to an issue or pull request.

## Issues Commands

### Create Issue

```bash
gh issue create --repo OWNER/REPO --title "Title" --body "Description" [--label label1,label2]
```

Returns the issue URL on success.

### List Issues

```bash
gh issue list --repo OWNER/REPO [--label LABEL] [--state open|closed|all]
```

## Common Workflows

### Find First Project for a Repo

1. Extract owner from repo string (OWNER/REPO)
2. List projects for that owner
3. Use the first project's number

### Auto-detect Repo from Git

1. Try to get 'origin' remote
2. If no origin, get first available remote
3. Parse URL to extract owner/repo
4. Handle both HTTPS and SSH URLs

### Sync Tasks to Project

1. Verify gh CLI authentication
2. Determine target repo (provided or auto-detect)
3. Determine target project (provided or find first)
4. For each task:
   - Create GitHub issue with title and body
   - Get issue URL from creation response
   - Add issue to project using issue URL

## Error Handling

Common errors:
- `gh: command not found` - gh CLI not installed
- Authentication errors - run `gh auth login`
- Project not found - verify owner and project number
- Rate limiting - GitHub API has rate limits
- Invalid repo format - must be `owner/repo`

## URL Formats

### HTTPS
```
https://github.com/owner/repo.git
https://github.com/owner/repo
```

### SSH
```
git@github.com:owner/repo.git
```

Both should parse to `owner/repo` format.

## Task List Formats

### Markdown Checkbox Format
```markdown
- [ ] Task 1
- [ ] Task 2
- [x] Completed task (skip this)
```

### JSON Format
```json
[
  {
    "title": "Task 1",
    "body": "Optional description",
    "labels": ["enhancement", "priority:high"]
  }
]
```
