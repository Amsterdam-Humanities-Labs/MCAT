Review the entire MCAT codebase for code quality, consistency, potential bugs, and best practices. This is a pywebview desktop app with a Python backend and Svelte 5 frontend.

## Scope

Review both backend (`pywebview-app/backend/`) and frontend (`pywebview-app/frontend/src/`) code.

## Review Checklist

### Backend (Python)
- **Dead code**: Unused imports, functions, variables, or modules
- **Error handling**: Missing or inconsistent error handling, bare excepts, swallowed exceptions
- **Thread safety**: Race conditions in shared state, missing locks, unsafe concurrent access
- **Resource leaks**: Unclosed files, connections, or drivers; missing cleanup in error paths
- **Data consistency**: State that can get out of sync (e.g., project.json vs in-memory state)
- **API design**: Inconsistent response formats, missing validation, unclear error messages
- **Naming**: Inconsistent naming conventions (should be snake_case throughout)

### Frontend (Svelte 5 / TypeScript)
- **Svelte 5 patterns**: Correct use of `$state`, `$derived`, `$effect`, `$props`, `$bindable`; no Svelte 4 patterns like `$:` or `export let`
- **Memory leaks**: Missing cleanup in `$effect`, unsubscribed event listeners, intervals not cleared
- **Props consistency**: Consistent prop naming (snake_case for data from backend, camelCase for component props)
- **Component boundaries**: Components doing too much, API calls in leaf components, store access in wrong places
- **Type safety**: Missing types, `any` usage, unchecked nulls
- **Accessibility**: Missing ARIA attributes, keyboard navigation gaps
- **CSS/Theme**: Hardcoded colors instead of theme tokens, inconsistent spacing

### Cross-cutting
- **Security**: Command injection, path traversal, XSS, unsafe file operations
- **Performance**: N+1 patterns, unnecessary re-renders, large data in memory
- **Consistency**: Similar patterns handled differently in different places
- **TODOs/FIXMEs**: Outstanding items that need attention

## Output Format

Organize findings by severity:

1. **Bugs** - Issues that cause incorrect behavior or crashes
2. **Security** - Potential vulnerabilities
3. **Performance** - Bottlenecks or wasteful patterns
4. **Code quality** - Dead code, inconsistencies, maintainability issues
5. **Minor** - Style nits, naming, small improvements

For each finding, include:
- File path and line number
- What the issue is
- Why it matters
- Suggested fix (brief)
