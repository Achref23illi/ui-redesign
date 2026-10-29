# What makes a UI look AI-generated — and the fix

These are the defaults a model reaches for when nobody made a decision. Each one alone is
survivable; four together read as "vibe-coded". Fix them in the layer where they live.

| Tell | Why it reads as slop | Fix (layer) |
|---|---|---|
| Purple → blue or pink → orange gradients on backgrounds, buttons, text | nobody chose a brand colour | one accent from the brand, flat; a glow only behind the top of the page (colour) |
| Glow and neon shadows on cards and buttons | decoration standing in for hierarchy | 2–3 neutral shadows or hairlines (depth) |
| Emoji as icons (🚀 📊 ✨) | no icon system | one icon set, one stroke, labels (icons) |
| One font at one weight for everything, or 4 fonts | no type decisions | one family or one display + UI pair, 2–3 weights, one scale (type) |
| "Welcome back!! 👋" / "Supercharge your workflow 🚀" headlines | template copy | the user's name or the screen's real job in plain words (type) |
| Everything centred, hero to footer | no grid | left-aligned text blocks on one edge; centre only short hero lines (shape) |
| Cards inside cards inside cards | boxes used to group text | one card level; group with space and titles (shape) |
| Five radii on one screen (4, 6, 10, 12, 24) | values typed by hand | one radius personality from tokens (shape) |
| Grey boxes, gradients or icons where photos should be | no real content | real images at fixed ratios (imagery) |
| Three or four accent colours (blue buttons, green badges, purple tags, orange links) | colour as decoration | one accent for action; state colours only for state (colour) |
| A badge, pill or chip on every row | signalling everything = nothing | states as icons; words only for problems (components) |
| Icons beside every heading and label | decoration | icons only on actions and nav (icons) |
| Stat cards with a coloured icon disc + big number + "↑ 12%" + sparkline, ×8 | dashboard template | one hero figure per card; the rest as a table (data) |
| Gradient text on headings | effect over meaning | solid ink; let size and weight carry it (type) |
| Glass panels over a flat colour | glass with nothing to refract | glass only over moving content; solid surfaces elsewhere (depth) |
| Shadows on dark mode surfaces | invisible depth, muddy edges | lighter surfaces and hairlines (depth) |
| Buttons 52–60 px tall everywhere, full width everywhere | mobile defaults on every screen | 44 / 40 / 36, full width only for the one decision of a flow (components) |
| A spinner in an empty page | no loading design | a skeleton of the final layout (components) |
| "Something went wrong" + OK | no error design | the cause in one line + Retry (components) |
| Lorem ipsum, John Doe, $1,234.56, 99.9 % uptime | fake data | the product's real copy and plausible real numbers (imagery/data) |
| Random illustrations from three styles | asset grab-bag | one illustration style or none (imagery) |
| Huge hero, then twelve equal feature cards with icons | landing-page template | 3–5 sections, each with one idea and one visual proof (shape) |
| Every element animates in on scroll | motion as filler | one animation per change; content is just there (depth) |

## The 30-second test

Screenshot the screen, shrink it to 25 %, and answer:

1. What is the one thing this screen is for? Is it the most visible thing?
2. How many colours do you see? (More than ink + grey + one accent + one state = too many.)
3. How many font sizes? (More than 4 on one screen = too many.)
4. Do all corners look like the same hand drew them?
5. Is there anything decorative you could delete without losing information?
