# Design system: merge, build, migrate

## 1. What "one design system" means here

| Tier | Holds | Who reads it |
|---|---|---|
| **Primitives** | the raw ramps: `gray-50…950`, `accent-50…950`, state hues, the type, space, radius, shadow and duration scales | only the semantic tier |
| **Semantic** | roles: `bg`, `surface`, `surface-2`, `text`, `text-muted`, `text-subtle`, `border`, `border-strong`, `accent`, `accent-hover`, `on-accent`, `success`, `warning`, `danger`, `info`, `focus`, `overlay` | components |
| **Component** (optional) | `button-height-md`, `card-padding`, `input-radius` … | one component each |

A dark mode, a second brand or a "pro" space is a **new set of semantic values over the same
primitives**, never forked components.

## 2. Healthy sizes (what the merge aims for)

| Scale | Keep | Typical values |
|---|---|---|
| Neutrals | 11 steps + white + black | OKLab L 0.985 0.967 0.922 0.87 0.708 0.556 0.439 0.371 0.269 0.205 0.145 |
| Accent | 1 hue, 11 steps (use 2–3) | the brand colour at 500 or 600 |
| States | success, warning, danger, info | one step each for text, one tint for backgrounds |
| Type sizes | 6–9 | 12 13 14 16 18 20 24 30 (+ 36 48 60 72 for marketing) |
| Weights | 2–3 | 400 · 500 or 600 · 700 |
| Line heights | 3 | 1.15 titles · 1.4 UI · 1.6 reading |
| Radii | 3–4 + full | sharp 4 6 8 · soft 8 12 16 · round 12 20 28 |
| Spacing | 4-pt | 4 8 12 16 20 24 32 40 48 64 80 96 128 |
| Shadows | 2–3 | sm (controls) · md (popovers) · lg (dialogs) |
| z-index | 6 named | base 0 · sticky 10 · dropdown 20 · overlay 40 · modal 50 · toast 60 |
| Durations | 3 | 150 fast · 220 base · 360 slow |
| Breakpoints | 3–4 | 640 · 768 · 1024 · 1280 |

## 3. Merging a drifted system, step by step

1. `python3 scripts/audit.py <repo> --propose redesign-tokens.md` — the draft maps every
   legacy value to a proposed token.
2. **Collapse near-duplicates** to the most-used member of each group (`#0f172a`,
   `#111827`, `#1a1a2e` → `gray-900`). The audit lists the groups.
3. **Rebuild the neutral ramp** at fixed lightness with the project's average tint (the
   proposal does this), so greys stay warm or cool as the brand was.
4. **One accent.** The most-used chromatic family is usually the brand; confirm with the user.
   Other chromatic families become states (red → danger, green → success, amber → warning) or
   go. Kill the decorative third and fourth accent.
5. **Opacity sprawl → 3–4 alpha steps** per colour you really need translucent
   (`/8 /16 /32 /64`), or replace with solid ramp steps (better contrast, easier dark mode).
6. **Snap the scales** (type, radius, spacing) with the proposal's tables; values that sit
   between two steps go to the one that matches the component's role, not the nearest
   number.
7. Write the token file (§4), **alias every legacy token name to its new token** (§5), commit.

## 4. Token file formats

### CSS variables (any stack)

```css
:root {
  /* primitives */
  --gray-50: oklch(0.985 0.002 85); --gray-100: oklch(0.967 0.003 85); /* … */ --gray-950: oklch(0.145 0.004 85);
  --accent-500: oklch(0.62 0.17 35); --accent-600: oklch(0.56 0.17 35);
  /* semantic */
  --bg: var(--gray-50); --surface: #fff; --text: var(--gray-950); --text-muted: var(--gray-500);
  --border: color-mix(in oklch, var(--gray-950) 9%, transparent);
  --accent: var(--accent-600); --on-accent: #fff; --focus: var(--accent-500);
  --success: oklch(0.6 0.13 150); --warning: oklch(0.75 0.15 75); --danger: oklch(0.58 0.2 27);
  --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px; --radius-full: 999px;
  --shadow-sm: 0 1px 2px rgb(20 20 30 / .06); --shadow-md: 0 6px 20px rgb(20 20 30 / .08); --shadow-lg: 0 24px 60px rgb(20 20 30 / .14);
}
[data-theme="dark"] { --bg: var(--gray-950); --surface: var(--gray-900); --text: var(--gray-50); --text-muted: var(--gray-400); }
```

### Tailwind v4 (`@theme` in the main CSS)

```css
@import "tailwindcss";
@theme {
  --color-bg: var(--bg); --color-surface: var(--surface); --color-ink: var(--text); --color-muted: var(--text-muted);
  --color-accent: var(--accent); --color-on-accent: var(--on-accent);
  --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px;
  --text-xs: 12px; --text-sm: 13px; --text-base: 14px; --text-md: 16px; --text-lg: 20px; --text-xl: 24px; --text-2xl: 32px;
  --font-sans: "Geist", system-ui, sans-serif; --font-display: "Instrument Serif", serif;
}
```

### Tailwind v3 (`tailwind.config`)

```js
theme: { extend: {
  colors: { bg: 'var(--bg)', surface: 'var(--surface)', ink: 'var(--text)', muted: 'var(--text-muted)', accent: { DEFAULT: 'var(--accent)', fg: 'var(--on-accent)' } },
  borderRadius: { sm: 'var(--radius-sm)', md: 'var(--radius-md)', lg: 'var(--radius-lg)' },
  fontSize: { xs: ['12px', '16px'], sm: ['13px', '18px'], base: ['14px', '20px'], md: ['16px', '24px'], lg: ['20px', '28px'], xl: ['24px', '30px'], '2xl': ['32px', '36px'] },
} }
```

### shadcn/ui

Keep its variable names (`--background --foreground --card --primary --primary-foreground
--muted --muted-foreground --border --input --ring --radius`) and point them at your semantic
tokens. Don't rename shadcn's API; map onto it.

### React Native / Expo (`theme.ts`)

```ts
export const color = { bg: '#F5F2ED', surface: '#FFFFFF', text: '#161514', muted: '#8C867D', border: 'rgba(22,21,20,0.08)', accent: '#161514', onAccent: '#FFFFFF', danger: '#C93B2B' } as const;
export const space = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32, 10: 40, 12: 48 } as const;
export const radius = { sm: 8, md: 12, lg: 16, xl: 24, full: 999 } as const;
export const type = { caption: { fontSize: 12, lineHeight: 16 }, body: { fontSize: 15, lineHeight: 21 }, title: { fontSize: 20, lineHeight: 26, fontWeight: '600' }, display: { fontSize: 34, lineHeight: 38 } } as const;
```

### SwiftUI

```swift
extension Color { static let bg = Color("bg"); static let ink = Color("ink"); static let muted = Color("muted"); static let accent = Color("AccentColor") }
enum Space { static let s = 8.0, m = 16.0, l = 24.0 }   // colours live in the asset catalog with Any/Dark appearances
```

### Flutter

```dart
final theme = ThemeData(useMaterial3: true, colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF161514), surface: const Color(0xFFF5F2ED)),
  textTheme: const TextTheme(bodyMedium: TextStyle(fontSize: 15, height: 1.4), titleLarge: TextStyle(fontSize: 20, fontWeight: FontWeight.w600)));
```

## 5. Migration without breaking anything

1. **Alias first.** Old names keep working: `--primary-old: var(--accent);`,
   `colors: { purple: { 600: 'var(--accent)' } }`, `export const COLORS = { primary: color.accent, … }`.
   The app looks the same or better on day one; nothing is deleted.
2. **Codemods for the obvious ones** (always review the diff):
   ```bash
   # every hard-coded near-black → the token (preview with -n first)
   rg -l '#(0f172a|111827|1a1a2e)' src | xargs sed -i '' -E 's/#(0f172a|111827|1a1a2e)/var(--text)/g'
   # Tailwind arbitrary sizes → scale classes
   rg -l 'text-\[13px\]' src | xargs sed -i '' 's/text-\[13px\]/text-sm/g'
   ```
3. **Migrate by file, worst first** — the audit ends with the files holding the most raw
   values. One commit per area (`redesign(tokens): checkout uses tokens`).
4. **Guard it** so drift can't come back:
   - Stylelint: `"color-no-hex": true` everywhere except the token file.
   - ESLint: `no-restricted-syntax` on `/#[0-9a-f]{3,8}/i` string literals in components, or
     `tailwindcss/no-arbitrary-value`.
   - A CI step: `python3 scripts/audit.py . --json audit.json` and fail if a category grows.
5. **Remove the aliases last**, in their own commit, once `rg` finds no legacy name.

## 6. Contrast and accessibility, as numbers

- Text ≥ 4.5:1, large text (≥ 24 px, or 19 px bold) and UI parts (borders of inputs, icons that
  carry meaning) ≥ 3:1. Muted text on a tinted ground is the usual failure — check it.
- Focus ring: 2 px `--focus` with 2 px offset, visible on every interactive element.
- Never colour alone for state: add an icon, a word or a shape.
- Tap targets ≥ 44 × 44 pt (hit-slop when the visual is smaller).
- Respect `prefers-reduced-motion` and the platform's text-size setting.
