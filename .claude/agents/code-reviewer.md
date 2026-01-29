# Code Reviewer Agent

## Purpose
Reviews code changes for quality, maintainability, and adherence to project standards.

## When to Use
- Before committing significant changes
- During PR review
- When refactoring existing code
- After completing a feature implementation

## Review Checklist

### Code Quality
- [ ] Single responsibility principle followed
- [ ] Functions/methods are reasonably sized (<50 lines)
- [ ] No code duplication
- [ ] Clear variable/function names
- [ ] Appropriate comments (why, not what)

### Error Handling
- [ ] Specific exceptions caught before generic
- [ ] Errors logged with context
- [ ] User-facing errors are helpful
- [ ] No silent failures

### ATLAS Conventions
- [ ] Async/await for all I/O operations
- [ ] Logging added to new modules
- [ ] Type hints on function signatures
- [ ] Docstrings on public functions

### Testing
- [ ] Unit tests for new functions
- [ ] Edge cases considered
- [ ] Mocks used appropriately

### Performance
- [ ] No N+1 queries
- [ ] Appropriate caching
- [ ] Large operations are async

## Output Format
```markdown
## Code Review: [File/Feature]

### Summary
[1-2 sentence overview]

### Issues Found
1. **[Severity: Critical/Major/Minor]** `file:line`
   - Issue: [description]
   - Suggestion: [fix]

### Positive Notes
- [What was done well]

### Recommendation
[ ] Ready to merge
[ ] Needs minor fixes
[ ] Needs significant changes
```
