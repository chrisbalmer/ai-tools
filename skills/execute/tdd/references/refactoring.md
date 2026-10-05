# Refactor candidates

After a TDD cycle reaches GREEN, look for:

- **Duplication** → extract function/class
- **Long methods** → break into private helpers (keep tests on the public interface)
- **Shallow modules** → combine or deepen (see [deep-modules.md](deep-modules.md))
- **Feature envy** → move logic to where the data lives
- **Primitive obsession** → introduce value objects
- **Existing code the new code reveals as problematic** — TDD is the best architecture sensor you have. If a refactor candidate appears more than two cycles in a row in the same area, raise it as input for `/improve-codebase-architecture`.

## When refactoring crosses a module boundary

If the refactor pulls behavior across a seam (extracting a new module, collapsing two into one), stop and check:

- Is this a deepening (good — pulls complexity inward)?
- Is this just moving complexity sideways (bad — call it out and skip)?

Apply the **deletion test** from [[language/improve-codebase-architecture/references/LANGUAGE.md]]: if you deleted the new module, would complexity vanish (it was a pass-through) or reappear across N callers (it was earning its keep)?
