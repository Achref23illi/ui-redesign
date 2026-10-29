# Redesigning a big, existing product

Ten screens are a design task. Two hundred screens across a web app, an admin and a mobile
app are a migration. Treat them like one.

## 1. Inventory (before any opinion)

- **Routes and screens.** List them from the router (`app/**/page.tsx`, `pages/`, `routes/`,
  Expo `app/`, navigation stacks, storyboard/SwiftUI views). Write `redesign/inventory.md`:
  route · what it is for · traffic guess (high / mid / low) · shared components it uses.
- **Components.** Count how many buttons, inputs, cards, modals and tables exist and how many
  versions of each. `rg -c "<button|<Button" src`, `rg -l "Modal|Dialog" src`. Three button
  components is the most common finding.
- **Systems in play.** Tailwind config, CSS modules, styled-components, a UI kit (MUI, Chakra,
  shadcn, NativeBase, Tamagui), inline styles. The audit's `inline style objects` and
  `tailwind arbitrary values` show how much bypasses any system.
- **Screens to hand-craft:** the 3–5 with the most traffic or the most money (home, the core
  task, checkout/billing, onboarding). Everything else gets the system and a check.

## 2. Branching for many changes

```
main ─────────────────────────────────────────────── (untouched)
  └─ redesign/design-system      tokens + aliases + primitives
       ├─ redesign/app-shell     header, sidebar, tab bar, layout grid
       ├─ redesign/core-flows    the 3–5 key screens by hand
       └─ redesign/sweep-<area>  remaining screens per area
```

- Every branch starts from `redesign/design-system`, never from `main`, once tokens exist.
- One area per branch keeps reviews under ~400 changed lines where possible.
- Rebase the redesign branches on `main` regularly so the user's ongoing work is not lost; on
  conflicts in screen logic, the user's version wins and the redesign re-applies styling.
- Merging any of it into `main` is the user's decision. Offer a PR; don't merge.

## 3. Order of work

1. **Tokens + aliases** (nothing looks broken, some things already look better).
2. **Primitives:** Button, IconButton, Input, Select, Checkbox, Switch, Card, Row/ListItem,
   Tabs, Badge, Avatar, Dialog/Sheet, Toast, Skeleton, EmptyState. One component per role;
   the duplicates become thin wrappers around it, then go.
3. **Patterns:** page header, sidebar/tab bar, data table, form layout, filters bar, settings
   list, stat card.
4. **Key screens by hand** (recipes from ui-craft for mobile; product references for web).
5. **Sweep** every other screen through primitives and patterns; most need only imports
   changed and arbitrary values removed.
6. **Remove legacy aliases and dead components.** `rg` must find none of the old names.

## 4. Codemods that save days

```bash
# list every arbitrary Tailwind value with its count (the worst offenders first)
rg -o --no-filename '\b[a-z-]+-\[[^\]]+\]' src | sort | uniq -c | sort -rn | head -40
# swap a deprecated component import for the primitive
rg -l "from '@/components/OldButton'" src | xargs sed -i '' "s#@/components/OldButton#@/ui/button#"
# find inline style objects in React Native screens (migrate to StyleSheet + tokens)
rg -n "style=\{\{" app src | wc -l
```

Use `jscodeshift` / `ts-morph` when a prop API changes (`<OldButton kind="primary">` →
`<Button variant="primary">`). Always read the diff before committing.

## 5. Proof that nothing broke

- **Before/after screenshots** of every route: `scripts/shots.py` per branch, compared pairwise.
- **Visual regression** in CI when the project has it (Playwright `toHaveScreenshot`,
  Chromatic, Percy, Loki for React Native): update baselines only on redesign branches.
- **Behaviour:** run the existing test suite on every redesign commit; a redesign commit that
  changes a test's logic is a bug.
- **Accessibility:** axe or Lighthouse on the key screens before and after; scores must not drop.
- **Performance:** fonts (≤ 2 files above the fold), images (sized, lazy below the fold),
  backdrop filters (≤ 3 on screen at once, none on long scrolling lists).

## 6. Rolling it out

- **Flag the theme** when the product is live and the redesign is big: a `data-theme="v2"`
  attribute or a `ThemeProvider` switch reading a feature flag, so v1 and v2 ship together
  and the team can flip, compare and roll back.
- **Screens migrate behind the same flag**; the flag goes when every screen is v2.
- **Write the system down** in `DESIGN.md`: the five decisions, the tokens table, the
  component list with when to use each, and the rules the lint guard enforces.

## 7. Monorepos and multiple platforms

- One token source (JSON or TS) → generated outputs: CSS variables for web, `theme.ts` for
  React Native, an asset catalog for iOS, `ThemeData` for Flutter. Style Dictionary or a
  30-line script both work.
- Share the decisions, not the components: web, iOS and Android each keep native controls
  and platform conventions (sheets, back gestures, tab bars), styled by the same tokens.
