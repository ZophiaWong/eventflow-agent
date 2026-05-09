---
name: feature-slice
description: Use this skill before implementing any non-trivial feature. It turns a vague feature request into a small, testable, interview-friendly development slice with explicit scope, files, acceptance criteria, and tests.
---

# Feature Slice Skill

Use this skill before coding any feature that touches more than one file, changes LangGraph workflow behavior, changes schemas, or introduces new tests.

## Workflow

1. Restate the feature in one sentence.
2. Identify the smallest useful slice.
3. Define what is in scope.
4. Define what is explicitly out of scope.
5. List files likely to inspect.
6. List files allowed to modify.
7. List files that must not be modified.
8. Define input and output schemas.
9. Define acceptance criteria.
10. Define tests required.
11. Define the interview takeaway.

## Output Format

```md
# Feature Slice

## Goal

...

## Smallest Useful Slice

...

## In Scope

...

## Out of Scope

...

## Files to Inspect

...

## Files Allowed to Modify

...

## Files Not Allowed to Modify

...

## Input / Output Contract

...

## Acceptance Criteria

...

## Tests Required

...

## Interview Takeaway

...
```
