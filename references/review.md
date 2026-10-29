# Fast design review

For "what's wrong with my UI?" when the user wants a verdict, not a redesign yet.

1. **Screens:** `scripts/shots.py <url> <routes…> --out shots/review` (or the user's
   screenshots). Read the contact sheets, not single files.
2. **System:** `scripts/audit.py <repo>` if the code is available — the numbers make the
   review concrete ("37 font sizes", not "inconsistent type").
3. **Score each layer 0–2** (0 broken · 1 inconsistent · 2 designed): type, colour, shape &
   space, imagery, icons, components & states, data, depth & motion. The total out of 16 is
   the headline; the lowest layers are where to start.
4. **Report as a table**, ten findings at most, global ones first:

| # | Screen | Layer | What is wrong (with a number) | Fix (with a number) |
|---|---|---|---|---|
| 1 | all | Type | 9 sizes and 4 weights on the dashboard card | 4 sizes from the 8-step scale, 2 weights |
| 2 | all | Colour | blue buttons, purple tags, green links: 3 accents | ink for actions, one accent for active state |
| 3 | Home | Imagery | product tiles are grey boxes | 4:5 photos, cover, focal point on the face |

5. End with **what to do first** (usually: tokens, then type, then colour) and offer the
   redesign on a new branch.
