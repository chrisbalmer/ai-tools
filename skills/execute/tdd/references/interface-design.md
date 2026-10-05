# Interface design for testability

Good interfaces make testing natural.

**1. Accept dependencies, don't create them**

```typescript
// Testable
function processOrder(order, paymentGateway) {}

// Hard to test
function processOrder(order) {
  const gateway = new StripeGateway();
}
```

**2. Return results, don't produce side effects**

```typescript
// Testable
function calculateDiscount(cart): Discount {}

// Hard to test
function applyDiscount(cart): void {
  cart.total -= discount;
}
```

**3. Small surface area**

- Fewer methods = fewer tests needed
- Fewer params = simpler test setup

## Cross-reference

When in doubt about interface shape, defer to [[language/improve-codebase-architecture/references/LANGUAGE.md]]:

- **Depth** is leverage at the interface — small interface, lots of behavior behind it
- The **interface is the test surface** — tests cross the same seam as callers
- **One adapter means a hypothetical seam** — don't introduce dependency injection where there's only one real adapter
