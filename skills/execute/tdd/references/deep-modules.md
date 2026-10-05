# Deep modules

From John Ousterhout's *A Philosophy of Software Design*. See [[language/improve-codebase-architecture/references/LANGUAGE.md]] for the full vocabulary.

**Deep module** = small interface + lots of implementation.

```
┌─────────────────────┐
│   Small Interface   │  ← Few methods, simple params
├─────────────────────┤
│                     │
│                     │
│  Deep Implementation│  ← Complex logic hidden
│                     │
│                     │
└─────────────────────┘
```

**Shallow module** = large interface + little implementation. Avoid.

```
┌─────────────────────────────────┐
│       Large Interface           │  ← Many methods, complex params
├─────────────────────────────────┤
│  Thin Implementation            │  ← Just passes through
└─────────────────────────────────┘
```

When designing interfaces, ask:

- Can I reduce the number of methods?
- Can I simplify the parameters?
- Can I hide more complexity inside?

## Why this matters for testing

- A deep module has one interface to test. A shallow module forces you to test through three or four pass-through interfaces, each of which can drift independently.
- The **interface is the test surface** — if you want to test past the interface, the module is probably shallow.
- Tests on a deep module survive internal refactors. Tests on shallow modules break the moment the pass-through structure changes.
