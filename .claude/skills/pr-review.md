# PR Review Workflow

## Overview
Code review checklist for pull requests in ATLAS and Baby Brains projects.

## Before Creating PR

### 1. Self-Review
```bash
# View all changes
git diff main...HEAD

# Check for debug code
git diff main...HEAD | grep -E "(console\.log|print\(|debugger|TODO)"

# Run tests
pytest

# Run linting (if configured)
ruff check .
```

### 2. Commit Hygiene
- Atomic commits (one logical change per commit)
- Descriptive commit messages
- No merge commits in feature branch

### 3. Branch Naming
- `feature/<description>` - New features
- `fix/<description>` - Bug fixes
- `refactor/<description>` - Code improvements
- `docs/<description>` - Documentation only

## Creating PR

### Title Format
```
<type>: <short description>

Types: feat, fix, refactor, docs, test, chore
```

### Body Template
```markdown
## Summary
<1-3 bullet points describing the change>

## Test plan
- [ ] Unit tests pass
- [ ] Manual verification: <describe>
- [ ] No regressions in <related feature>

## Notes
<Any context reviewers need>
```

## Review Checklist

### Code Quality
- [ ] Follows ATLAS conventions (async/await, error handling)
- [ ] No unnecessary complexity
- [ ] No code duplication
- [ ] Clear naming

### Testing
- [ ] Tests added for new functionality
- [ ] Edge cases covered
- [ ] Tests actually test behavior (not implementation)

### Security
- [ ] No hardcoded secrets
- [ ] Input validation where needed
- [ ] No SQL injection / command injection risks

### Performance
- [ ] No obvious N+1 queries
- [ ] Async for I/O operations
- [ ] No blocking calls in voice pipeline

### Documentation
- [ ] Public functions have docstrings
- [ ] Complex logic has comments
- [ ] README updated if needed

## After Merge

```bash
# Delete local branch
git branch -d feature/my-feature

# Update main
git checkout main && git pull
```

## Greptile Integration (Future)

When Greptile is configured:
- Automatic in-line comments on PRs
- Custom rules enforced
- PR summaries with diagrams
- Pattern learning from previous reviews
