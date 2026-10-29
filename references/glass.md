# Liquid glass, done right

## When

- **Yes:** floating chrome over content that moves under it — a tab bar over a scrolling
  feed, a toolbar over a photo, media controls over video, a map's search pill, a product
  page's back/heart discs over the hero image.
- **No:** every card, sidebars on flat backgrounds, text-heavy panels, long scrolling lists of
  glass rows (expensive and unreadable), anything over a rainbow mesh added just so the
  glass "shows". If there is nothing behind it, use a solid surface.

## The cheap version (works everywhere)

```css
.glass {
  background: rgb(255 255 255 / .42);                      /* dark UI: rgb(24 24 27 / .45) */
  backdrop-filter: blur(16px) saturate(1.8);
  -webkit-backdrop-filter: blur(16px) saturate(1.8);
  border-radius: 999px;
  box-shadow:
    inset 0 0 0 1px rgb(255 255 255 / .65),                /* rim */
    inset 0 1.5px 1px rgb(255 255 255 / .95),              /* top highlight */
    inset 0 -2px 8px rgb(255 255 255 / .35),               /* lower glow */
    0 14px 34px rgb(30 24 18 / .14), 0 2px 6px rgb(30 24 18 / .06);
}
```

## The lens version (real refraction, Chromium)

The edge of real glass bends what is behind it. Generate a displacement map for the element's
shape — neutral in the middle, pushing inward along a band at the rounded edge — and use it as
an SVG filter inside `backdrop-filter`. Put the filter in `objectBoundingBox` units so it
stays aligned at any zoom.

```js
function lensMap(w, h, r, band = Math.min(h * .45, 22), D = Math.min(14, h * .3)) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d'), im = g.createImageData(w, h);
  const sd = (x, y) => { const qx = Math.abs(x - w / 2) - (w / 2 - r), qy = Math.abs(y - h / 2) - (h / 2 - r);
    return Math.hypot(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - r; };
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const d = sd(x + .5, y + .5); let dx = 0, dy = 0;
    if (d < 0 && -d < band) {
      const nx = sd(x + 1.5, y + .5) - sd(x - .5, y + .5), ny = sd(x + .5, y + 1.5) - sd(x + .5, y - .5), L = Math.hypot(nx, ny) || 1;
      const k = (1 + d / band) ** 2 * D; dx = -nx / L * k; dy = -ny / L * k;        // sample further inside near the rim
    }
    const i = (y * w + x) * 4; im.data[i] = 127.5 + 255 * dx / w; im.data[i + 1] = 127.5 + 255 * dy / h; im.data[i + 2] = 128; im.data[i + 3] = 255;
  }
  g.putImageData(im, 0, 0); return c.toDataURL();
}
function makeGlass(el, id) {
  const w = el.offsetWidth, h = el.offsetHeight, r = Math.min(h / 2, parseFloat(getComputedStyle(el).borderTopLeftRadius) || h / 2);
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); svg.setAttribute('width', 0); svg.setAttribute('height', 0); svg.style.position = 'absolute';
  svg.innerHTML = `<filter id="${id}" x="0" y="0" width="1" height="1" primitiveUnits="objectBoundingBox" color-interpolation-filters="sRGB">
    <feImage href="${lensMap(w, h, r)}" x="0" y="0" width="1" height="1" preserveAspectRatio="none" result="m"/>
    <feDisplacementMap in="SourceGraphic" in2="m" scale="1" xChannelSelector="R" yChannelSelector="G"/></filter>`;
  const root = el.getRootNode(); (root instanceof ShadowRoot ? root : document.body).appendChild(svg);
  el.style.backdropFilter = `url(#${id}) blur(3px) saturate(1.7) brightness(1.05)`;
}
```

Notes:
- `backdrop-filter: url(#…)` works in Chromium (Chrome, Edge, Electron). Safari and Firefox
  ignore it — keep the cheap version as the base and add the lens with `@supports` or a
  user-agent check.
- The filter must live in the same document or shadow root as the element.
- Rebuild the map when the element's size changes (ResizeObserver); cache by `w×h×r`.
- Keep text on glass ≥ 15 px, weight ≥ 500, with the frosted tint at ≥ 40 % so labels stay
  readable over busy photos.
- Budget: ≤ 3 glass elements on screen at once.

## Native

- **iOS 26+:** SwiftUI `.glassEffect()` and the system tab bar/toolbars already are liquid
  glass; don't fake it on top. Earlier iOS: `.background(.ultraThinMaterial)`.
- **React Native / Expo:** `expo-blur` `BlurView` (intensity 40–60, tint `light`/`dark`) +
  a 1 px white rim at 60 % + a soft shadow; `expo-glass-effect` where available.
- **Android:** `RenderEffect.createBlurEffect` (API 31+) on a snapshot behind the bar; a
  solid surface at 94 % below that.
