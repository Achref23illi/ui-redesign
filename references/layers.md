# The eight layers

Same layout, same data, one layer at a time. Each layer: read the rules, apply through tokens,
screenshot, compare, commit. If a layer makes something worse, revert that commit only.

---

## 1 · Type

**Goal:** the hierarchy reads with your eyes half closed.

- One family for the interface (Geist, Inter, Plus Jakarta Sans, DM Sans, Onest, Figtree,
  Public Sans, the system face) — or a pair: a display face for titles only (a serif such as
  Instrument Serif, Newsreader, Fraunces; or a grotesk with character) + the UI face for
  every control, label and number.
- One scale (product UI: 12 13 14 16 18 20 24 30; marketing adds 36 48 60 72). Every text
  node maps to a step; delete the in-betweens (15.5, 17, 19, 22…) unless the scale has them.
- 2–3 weights. Titles 600–700 (a display serif stays at 400), labels 500, text 400.
- Titles ≥ 32 px: tracking −1 to −3 %, line-height 1.05–1.2. Body: line-height 1.4–1.6,
  measure 60–75 characters.
- Numbers that change or align: `font-variant-numeric: tabular-nums`.
- Uppercase only for ≤ 12 px eyebrows/labels with +4–8 % tracking; never for titles or
  buttons ≥ 14 px.
- Secondary text is the muted colour, not a smaller size *and* lighter weight *and* grey.

**Code:** set the families and scale in tokens; replace arbitrary sizes (`text-[13px]` →
`text-sm`); one `h1…h6`/`Text` variant set; load fonts with `font-display: swap` and preload
the 1–2 files used above the fold.

**Commit:** `redesign(type): Geist for UI, Instrument Serif for titles, 8-step scale`

---

## 2 · Colour

**Goal:** colour means something.

- Ground + surface + ink from the neutral ramp. Warm or cool greys follow the brand; pure
  `#000` on pure `#fff` only for stark brands.
- **One accent** = the action and the active state. ≤ 3 uses per screen (primary button,
  active nav item, one selection). Links in the ink colour underlined, or the accent — not
  both.
- States: success, warning, danger, info — text colour plus a 8–14 % tint for backgrounds.
  Colour lives inside the number or the badge, not on the buttons around it.
- Borders: the ink at 6–10 % alpha, or a ramp step; never a saturated colour as a border
  except focus and error.
- Gradients: only a brand glow (a vertical fade of the brand colour behind the top of the
  page, ~30 % → 0 over 300–400 px) or inside imagery. No gradient buttons, no gradient
  text, no rainbow meshes.
- Dark mode: lift surfaces with lighter greys, not shadows; reduce accent saturation 10–20 %;
  text at 92–96 % white, muted at 60–70 %.

**Commit:** `redesign(colour): warm neutral ramp, ink actions, clay accent for state only`

---

## 3 · Shape & space

**Goal:** one hand drew every corner and every gap.

- One radius personality, ≤ 4 values: controls (8–12), cards (12–20), sheets/modals (20–28),
  pills (full). Nested corners: inner = outer − padding.
- 4-pt spacing everywhere. One gutter per breakpoint (16–20 phone, 24–32 tablet, 32–64
  desktop). Inside a card 16–24; between related items 8–12; between sections 24–32 in apps,
  96–160 on marketing pages.
- Group by proximity, not boxes: a title 8–12 above its content and 24–32 away from the
  previous section is a divider.
- Remove boxes that only group text. Cards are for objects (a product, a booking, a file).
- Align to edges: every block on the page starts on the same left line.

**Commit:** `redesign(shape): 8/16/full radii, 4-pt spacing, 24 gutter`

---

## 4 · Imagery

**Goal:** the content carries the screen.

- Real photos or the product's own media. Fixed ratios per role: fashion/social 4:5,
  video 16:9, posters 2:3, avatars 1:1, recipes 3:4, wide heroes 3:2 or 16:9.
- `object-fit: cover`, focal point set (`object-position`) so faces are never cut.
- The hero image goes full-bleed or to the gutter, not boxed with a border inside a card.
- Text on photos: a 40–60 % dark scrim from the bottom (or top), text ≥ 15 px, white.
- Empty or missing images: a tinted block in the layout's ratio with a 24 px icon, never a
  broken-image icon or a grey box with "Image".
- Illustration: one style for the whole product or none.

**Commit:** `redesign(imagery): 4:5 product photos, full-bleed hero with scrim`

---

## 5 · Icons

- One set (Lucide, Phosphor, SF Symbols, Material Symbols) at one stroke (1.5–2 px on 24).
- Sizes: 16 inline with 13–14 text, 20 in buttons and inputs, 24 in nav and headers.
- Every action icon has a visible label except home, search, back and close.
- No emoji as UI. No icon beside every heading or list label as decoration.
- Filled = active, outline = inactive (tab bars), never mixed otherwise.

**Commit:** `redesign(icons): Lucide 1.75 px, labelled actions, emoji removed`

---

## 6 · Components & states

| Component | Spec |
|---|---|
| Button | 44 primary · 40 default · 36 compact · 32 in tables; padding 16–20; one filled per view; secondary = tinted or outline; tertiary = text |
| Input | 40–44; label above 13/500; placeholder is an example, not the label; error text replaces help text |
| Select / combobox | same height as inputs; chevron 16; menu with 36–40 rows |
| Checkbox / radio / switch | 16–20 visual, 44 target; switch 44×26 |
| Card | padding 16–24, radius from the scale, one shadow or one border — never both strong |
| Table row | 40–48; numbers right-aligned, tabular; actions on hover in a ⋯ menu |
| Tabs / segmented | one active style (fill or underline), 32–40 tall |
| Dialog | 400–560 wide, title 18–20/600, one primary, Cancel as text or secondary |
| Toast | 40–54 pill or bar, auto-dismiss, optional Undo |

Every interactive component: **default, hover, focus-visible, pressed (scale 0.97–0.98 or
darker by one step), disabled (neutral fill + muted label, not a paler accent), loading
(spinner or skeleton in place, label kept)**. Every list or page: **loading skeleton, empty
(one line + one action), error (the cause + Retry)**.

**Commit:** `redesign(components): buttons 44/40/36, all states, skeletons and empty states`

---

## 7 · Data

- One hero figure per card or screen: 28–40/600 tabular, label 12–13 muted above, change as
  a small coloured value (+4.2 %) — green/red only inside the number.
- One chart per card, full width, no gridlines or very light ones, direct labels instead of a
  legend when ≤ 3 series, a range control under it (1D 1W 1M 1Y All).
- Bars: 6–16 px wide with 4–8 px gaps, radius 2–4 at the top only, one colour per series.
- Axis labels 11–12 muted; zero baseline visible; never truncate an axis to dramatise.
- Tables: right-align numbers, left-align text, units in the header, not in every cell.

**Commit:** `redesign(data): tabular figures, one chart per card, quiet axes`

---

## 8 · Depth, motion, glass

- Depth: flat with hairlines, or 2–3 soft shadows (sm controls, md popovers, lg dialogs).
  Dark mode: borders and lighter surfaces instead of shadows.
- Motion: one animation per change. Hover/press 150–200 ms, enter 200–300 ms ease-out, exit
  150 ms ease-in, page 300–400 ms. Drill-down slides, tasks rise, tabs cross-fade.
  `prefers-reduced-motion` turns it off.
- Glass: only for floating chrome over moving content — see `glass.md`.
- Nothing glows. No bounce on navigation. No parallax on app screens.

**Commit:** `redesign(depth): 3 shadow levels, glass tab bar over content, reduced motion`
