---
name: tdd
description: "Test-driven development with a strict red-green-refactor loop in vertical slices — one test → one implementation → repeat, never \"write all tests then all code.\" Tests must verify observable behavior through public interfaces, not implementation details. Used by ship-issue and milestone-builder implementer briefs when an issue lists testable behaviors (which is most of them). Reads CONTEXT.md for test-name vocabulary; respects ADRs in the area being changed. MANDATORY TRIGGERS: write tests for this, do this with TDD, red-green-refactor, write a failing test first, drive this with tests, test-first."
---

# Test-Driven Development

## Philosophy

**Tests verify behavior through public interfaces, not implementation details.** Code can change entirely; tests shouldn't. Read [tests.md](references/tests.md) for examples and [mocking.md](references/mocking.md) for mocking guidelines.

**Good tests** are integration-style: they exercise real code paths through public APIs. They describe *what* the system does, not *how* it does it. A test that reads like a specification ("user can checkout with valid cart") tells you exactly what capability exists. These tests survive refactors because they don't care about internal structure.

**Bad tests** are coupled to implementation. They mock internal collaborators, test private methods, or verify through external means (querying a database directly instead of using the interface). The warning sign: tests break when you refactor but behavior hasn't changed. If renaming an internal function fails tests, those tests were testing implementation, not behavior.

## Anti-pattern: horizontal slices

**Do not write all tests first, then all implementation.** This is "horizontal slicing" — treating RED as "write all tests" and GREEN as "write all code." It produces crap tests:

- Tests written in bulk test *imagined* behavior, not *actual* behavior
- You end up testing the *shape* of things (data structures, function signatures) rather than user-facing behavior
- Tests become insensitive to real changes — they pass when behavior breaks, fail when behavior is fine
- You outrun your headlights, committing to test structure before understanding the implementation

**Correct: vertical slices via tracer bullets.** One test → one implementation → repeat. Each test responds to what you learned from the previous cycle. Because you just wrote the code, you know exactly what behavior matters and how to verify it.

```
WRONG (horizontal):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

RIGHT (vertical):
  RED→GREEN: test1→impl1
  RED→GREEN: test2→impl2
  RED→GREEN: test3→impl3
  ...
```

## Workflow

### 1. Plan

When exploring the codebase, **read `CONTEXT.md`** so that test names and interface vocabulary match the project's language, and **respect any ADRs in `docs/adr/`** that touch the area you're working in.

Before writing any code:

- [ ] Confirm with the user (or the implementer brief) what interface changes are needed
- [ ] Confirm which behaviors to test, in priority order
- [ ] Identify opportunities for [deep modules](references/deep-modules.md) — small interface, deep implementation
- [ ] Design interfaces for [testability](references/interface-design.md)
- [ ] List the *behaviors* to test (not implementation steps)
- [ ] Get user approval on the plan (if invoked interactively); skip if invoked from an implementer brief that already locked the spec

Ask: "What should the public interface look like? Which behaviors are most important to test?"

**You can't test everything.** Focus testing effort on critical paths and complex logic, not every edge case.

### 2. Tracer bullet

Write ONE test that confirms ONE thing about the system:

```
RED:   Write test for first behavior → test fails
GREEN: Write minimal code to pass → test passes
```

This is your tracer bullet — proves the path works end-to-end.

### 3. Incremental loop

For each remaining behavior:

```
RED:   Write next test → fails
GREEN: Minimal code to pass → passes
```

Rules:

- One test at a time
- Only enough code to pass the current test
- Don't anticipate future tests
- Keep tests focused on observable behavior

### 4. Refactor

After tests pass, look for [refactor candidates](references/refactoring.md):

- [ ] Extract duplication
- [ ] Deepen modules (move complexity behind simple interfaces)
- [ ] Apply SOLID where natural
- [ ] Consider what the new code reveals about the existing code
- [ ] Run tests after each refactor step

**Never refactor while RED.** Get to GREEN first.

### Per-cycle checklist

```
[ ] Test describes behavior, not implementation
[ ] Test uses public interface only
[ ] Test would survive an internal refactor
[ ] Code is minimal for this test
[ ] No speculative features added
```

## Composition with other skills

- **Invoked from**: `/ship-issue` and `/milestone-builder` implementer briefs when the issue lists testable behaviors. The Implementer runs TDD against the listed behaviors rather than batching tests at the end of implementation.
- **Reads**: `CONTEXT.md` for test naming; `docs/adr/` for design constraints.
- **Hands off to**: `/diagnose` if a bug appears that the existing test suite doesn't catch — the diagnosis loop will produce a failing regression test that becomes the entry point for a new TDD cycle.
- **Surfaces to**: `/improve-codebase-architecture` when refactor candidates accumulate. "Tests are hostage to internal structure" is a signal of shallow modules.

## When NOT to use TDD

- **Prototyping or spike work** where the goal is to *learn what to build*, not to lock in behavior. Write the prototype first; if it survives, throw away the prototype and TDD the real version.
- **Trivial mechanical changes** (typo fixes, dependency bumps, formatting) — TDD has overhead and the change has no behavior surface.
- **UI work where the visual is the spec** — pair `/tdd` with manual or screenshot-based verification; pure TDD on visual code produces brittle tests.
