#!/usr/bin/env python3
"""audit.py — measure design-system drift in a codebase (standard library only).

Scans CSS/SCSS/Less, JS/TS/JSX/TSX, Vue, Svelte, Astro, HTML, Swift, Kotlin and Dart sources and counts every raw design
value it finds: colours, font families, font sizes, weights, line heights, letter spacing, radii, spacing, shadows,
z-index, breakpoints, durations and Tailwind utilities (including arbitrary values like text-[17px]).
Then it groups near-duplicate colours (OKLab distance), checks how much spacing sits off a 4-pt grid, compares every
category with healthy limits and says whether consolidating the design system is worth proposing.

  python3 scripts/audit.py <repo>                    # markdown report on stdout
  python3 scripts/audit.py <repo> --out audit.md      # write the report
  python3 scripts/audit.py <repo> --json audit.json   # machine-readable result as well
  python3 scripts/audit.py <repo> --propose tokens.md # also write a token proposal with a legacy → token mapping

It only reads files. It never edits the project.
"""
import argparse, collections, json, math, os, re, sys

SKIP_DIRS = {'node_modules', '.git', '.next', '.nuxt', '.svelte-kit', '.turbo', '.vercel', '.output', 'dist', 'build', 'out', 'coverage',
             'vendor', 'Pods', 'DerivedData', '.expo', '.gradle', 'android/app/build', '__pycache__', '.venv', 'venv', 'storybook-static', '.cache'}
EXTS = {'.css', '.scss', '.sass', '.less', '.pcss', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.vue', '.svelte', '.astro', '.html', '.swift', '.kt', '.dart'}
MAX_BYTES = 600_000

# ---------------------------------------------------------------- colour maths (sRGB → OKLab)
def _lin(c): c /= 255; return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def oklab(rgb):
    r, g, b = (_lin(v) for v in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s, 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)
def oklab2rgb(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3; m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3; s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    lin = (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s, -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)
    return tuple(round(255 * max(0, min(1, 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055))) for c in lin)
def hsl2rgb(h, s, l):
    h = (h % 360) / 360; s /= 100; l /= 100
    if s == 0: return (round(l * 255),) * 3
    q = l * (1 + s) if l < .5 else l + s - l * s; p = 2 * l - q
    def f(t):
        t %= 1
        return p + (q - p) * 6 * t if t < 1 / 6 else q if t < .5 else p + (q - p) * (2 / 3 - t) * 6 if t < 2 / 3 else p
    return tuple(round(f(h + o) * 255) for o in (1 / 3, 0, -1 / 3))
def hexstr(rgb): return '#%02x%02x%02x' % tuple(max(0, min(255, int(v))) for v in rgb)

# ---------------------------------------------------------------- patterns
RX = {
    'hex': re.compile(r'(?<![\w&/])#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b'),
    'rgb': re.compile(r'rgba?\(\s*(\d{1,3})[\s,]+(\d{1,3})[\s,]+(\d{1,3})(?:\s*[,/]\s*([\d.]+%?))?\s*\)'),
    'hsl': re.compile(r'hsla?\(\s*([\d.]+)(?:deg)?[\s,]+([\d.]+)%[\s,]+([\d.]+)%'),
    'flutter': re.compile(r'Color\(0x([0-9a-fA-F]{8})\)'),
    'family': re.compile(r'font-family\s*:\s*([^;}{]+)|fontFamily\s*[:=]\s*[\'"`]([^\'"`]+)'),
    'size': re.compile(r'font-size\s*:\s*([\d.]+)(px|rem|em|pt)\b|fontSize\s*[:=]\s*([\d.]+)\b|\.system\(size:\s*([\d.]+)|fontSize:\s*([\d.]+)'),
    'weight': re.compile(r'font-weight\s*:\s*(\d{3}|bold|normal)|fontWeight\s*[:=]\s*[\'"]?(\d{3}|bold|normal)'),
    'lh': re.compile(r'line-height\s*:\s*([\d.]+(?:px|rem|em|%)?)|lineHeight\s*[:=]\s*([\d.]+)'),
    'ls': re.compile(r'letter-spacing\s*:\s*(-?[\d.]+(?:px|em|rem)?)|letterSpacing\s*[:=]\s*(-?[\d.]+)'),
    'radius': re.compile(r'border(?:-[a-z]+)?-radius\s*:\s*([\d.]+)(px|rem|%)?|border\w*Radius\s*[:=]\s*([\d.]+)|cornerRadius\(\s*([\d.]+)|\.cornerRadius\(([\d.]+)|BorderRadius\.circular\(([\d.]+)'),
    'space': re.compile(r'\b(?:padding|margin|gap|row-gap|column-gap)(?:-(?:top|right|bottom|left|inline|block))?\s*:\s*([^;}{]+)|\b(?:padding|margin|gap)(?:Top|Right|Bottom|Left|Horizontal|Vertical)?\s*[:=]\s*([\d.]+)\b'),
    'shadow': re.compile(r'box-shadow\s*:\s*([^;}{]+)|boxShadow\s*[:=]\s*[\'"`]([^\'"`]+)'),
    'z': re.compile(r'z-index\s*:\s*(-?\d+)|zIndex\s*[:=]\s*(-?\d+)'),
    'media': re.compile(r'@media[^{]*?(?:min|max)-width\s*:\s*([\d.]+)(px|em|rem)'),
    'dur': re.compile(r'(?:transition|animation)(?:-duration)?\s*:[^;}{]*?([\d.]+)(ms|s)\b'),
    'var_def': re.compile(r'(--[\w-]+)\s*:'),
    'var_use': re.compile(r'var\(\s*(--[\w-]+)'),
    'tw_class': re.compile(r'(?:class(?:Name)?\s*=\s*|cn\(|clsx\(|cva\(|tw`)[\s\S]{0,4}?([\'"`])([^\'"`]{3,600})\1'),
    'inline_style': re.compile(r'style\s*=\s*\{\{'),
}
TW_COLOR = re.compile(r'^(?:[a-z]+:)*(bg|text|border|ring|fill|stroke|from|via|to|outline|divide|placeholder|accent|caret|decoration|shadow)-([a-z]+)-(50|[1-9]00|950)(?:/\d+)?$')
TW_ARB = re.compile(r'^(?:[a-z]+:)*([a-z-]+)-\[([^\]]+)\]$')
TW_SIZE = re.compile(r'^(?:[a-z]+:)*text-(xs|sm|base|lg|xl|[2-9]xl)$')
TW_ROUND = re.compile(r'^(?:[a-z]+:)*rounded(?:-[trblse]{1,2})?(?:-(none|sm|md|lg|xl|2xl|3xl|full))?$')
TW_SPACE = re.compile(r'^(?:[a-z]+:)*-?(?:p|px|py|pt|pr|pb|pl|ps|pe|m|mx|my|mt|mr|mb|ml|ms|me|gap|gap-x|gap-y|space-x|space-y)-(\d+(?:\.5)?|px)$')
TW_SHADOW = re.compile(r'^(?:[a-z]+:)*shadow(?:-(sm|md|lg|xl|2xl|inner|none))?$')
TW_WEIGHT = re.compile(r'^(?:[a-z]+:)*font-(thin|extralight|light|normal|medium|semibold|bold|extrabold|black)$')
TW_FONT = re.compile(r'^(?:[a-z]+:)*font-(sans|serif|mono|[a-z][\w-]*)$')
TW_BTN_HINT = re.compile(r'\b(?:h-(\d+)|py-(\d+(?:\.5)?))\b')

def to_px(v, unit):
    v = float(v); return v * 16 if unit in ('rem', 'em') else v * 4 / 3 if unit == 'pt' else v

def scan(root):
    D = collections.defaultdict(collections.Counter)    # category → value → count
    F = collections.defaultdict(lambda: collections.defaultdict(set))   # category → value → files
    stats = collections.Counter()
    for dp, dns, fns in os.walk(root):
        rel = os.path.relpath(dp, root)
        dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith('.') and os.path.join(rel, d) not in SKIP_DIRS]
        for fn in fns:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in EXTS or fn.endswith(('.min.js', '.min.css', '.d.ts', '.map')) or '.test.' in fn or '.spec.' in fn: continue
            p = os.path.join(dp, fn)
            try:
                if os.path.getsize(p) > MAX_BYTES: stats['skipped_big'] += 1; continue
                s = open(p, encoding='utf-8', errors='ignore').read()
            except OSError: continue
            rp = os.path.relpath(p, root); stats['files'] += 1; stats['ext' + ext] += 1
            def add(cat, val):
                D[cat][val] += 1; F[cat][val].add(rp)
            s_nocomment = re.sub(r'/\*[\s\S]*?\*/', ' ', s)
            for m in RX['hex'].finditer(s_nocomment):
                h = m.group(1)
                if len(h) in (3, 4): h = ''.join(c * 2 for c in h)
                a = int(h[6:8], 16) / 255 if len(h) == 8 else 1
                rgb = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
                add('color', hexstr(rgb) + ('' if a > .99 else f' / {a:.2f}'))
            for m in RX['rgb'].finditer(s_nocomment):
                r, g, b, a = m.groups(); rgb = tuple(int(x) for x in (r, g, b))
                if max(rgb) > 255: continue
                al = 1 if not a else (float(a[:-1]) / 100 if a.endswith('%') else float(a))
                add('color', hexstr(rgb) + ('' if al > .99 else f' / {al:.2f}'))
            for m in RX['hsl'].finditer(s_nocomment): add('color', hexstr(hsl2rgb(*(float(x) for x in m.groups()))))
            for m in RX['flutter'].finditer(s_nocomment): h = m.group(1); add('color', hexstr(tuple(int(h[i:i + 2], 16) for i in (2, 4, 6))))
            for m in RX['family'].finditer(s_nocomment):
                v = (m.group(1) or m.group(2) or '').strip()
                if v and 'var(' not in v and 'inherit' not in v: add('family', re.sub(r'[_-]?\d{3}\w*$|[_-](Regular|Medium|SemiBold|Bold|Light|Black|Italic)\w*$', '', v.split(',')[0].strip().strip('\'"')))
            for m in RX['size'].finditer(s_nocomment):
                if m.group(1): add('size', round(to_px(m.group(1), m.group(2)), 1))
                else:
                    v = m.group(3) or m.group(4) or m.group(5)
                    if v: add('size', round(float(v), 1))
            for m in RX['weight'].finditer(s_nocomment):
                v = m.group(1) or m.group(2); add('weight', {'bold': '700', 'normal': '400'}.get(v, v))
            for m in RX['lh'].finditer(s_nocomment): add('line-height', m.group(1) or m.group(2))
            for m in RX['ls'].finditer(s_nocomment): add('letter-spacing', m.group(1) or m.group(2))
            for m in RX['radius'].finditer(s_nocomment):
                if m.group(1): add('radius', ('%g%%' % float(m.group(1))) if m.group(2) == '%' else round(to_px(m.group(1), m.group(2) or 'px'), 1))
                else:
                    v = next((x for x in m.groups()[2:] if x), None)
                    if v: add('radius', round(float(v), 1))
            for m in RX['space'].finditer(s_nocomment):
                if m.group(1):
                    for tok in re.findall(r'(-?[\d.]+)(px|rem|em)\b', m.group(1)): add('space', abs(round(to_px(*tok), 1)))
                elif m.group(2): add('space', round(float(m.group(2)), 1))
            for m in RX['shadow'].finditer(s_nocomment):
                v = re.sub(r'\s+', ' ', (m.group(1) or m.group(2) or '').strip())
                if v and v != 'none' and 'var(' not in v: add('shadow', v[:90])
            for m in RX['z'].finditer(s_nocomment): add('z-index', int(m.group(1) or m.group(2)))
            for m in RX['media'].finditer(s_nocomment): add('breakpoint', round(to_px(m.group(1), m.group(2))))
            for m in RX['dur'].finditer(s_nocomment): add('duration', round(float(m.group(1)) * (1000 if m.group(2) == 's' else 1)))
            for m in RX['var_def'].finditer(s_nocomment): add('css-var', m.group(1))
            stats['var_uses'] += len(RX['var_use'].findall(s_nocomment))
            stats['inline_styles'] += len(RX['inline_style'].findall(s))
            if ext in ('.jsx', '.tsx', '.js', '.ts', '.vue', '.svelte', '.astro', '.html', '.mjs'):
                for m in RX['tw_class'].finditer(s):
                    for c in m.group(2).split():
                        if (k := TW_COLOR.match(c)): add('tw-color', f'{k.group(2)}-{k.group(3)}'); continue
                        if (k := TW_ARB.match(c)):
                            add('tw-arbitrary', c.split(':')[-1])
                            u, v = k.groups()
                            if u == 'text' and re.match(r'^[\d.]+(px|rem)$', v): add('size', round(to_px(*re.match(r'([\d.]+)(px|rem)', v).groups()), 1))
                            if u.startswith('rounded') and re.match(r'^[\d.]+(px|rem)$', v): add('radius', round(to_px(*re.match(r'([\d.]+)(px|rem)', v).groups()), 1))
                            if re.match(r'^#[0-9a-fA-F]{3,8}$', v): add('tw-arbitrary-color', v.lower())
                            continue
                        if (k := TW_SIZE.match(c)): add('tw-size', k.group(1)); continue
                        if (k := TW_ROUND.match(c)): add('tw-radius', k.group(1) or 'DEFAULT'); continue
                        if (k := TW_SPACE.match(c)): add('tw-space', k.group(1)); continue
                        if (k := TW_SHADOW.match(c)): add('tw-shadow', k.group(1) or 'DEFAULT'); continue
                        if (k := TW_WEIGHT.match(c)): add('tw-weight', k.group(1)); continue
                        if (k := TW_FONT.match(c)) and k.group(1) not in ('thin', 'extralight', 'light', 'normal', 'medium', 'semibold', 'bold', 'extrabold', 'black'): add('tw-font', k.group(1))
    return D, F, stats

# ---------------------------------------------------------------- analysis
def parse_color(v):
    h = v.split(' / ')[0]; return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

def color_groups(counter, thr=0.035):
    """Greedy grouping of the solid colours by OKLab distance; the most-used value leads each group.
    Opacity variants (`#fff / 0.6`) count toward their solid colour and are listed as alphas, not as duplicates."""
    solid, alphas = collections.Counter(), collections.defaultdict(set)
    for v, n in counter.items():
        base, _, a = v.partition(' / '); solid[base] += n
        if a: alphas[base].add(a)
    groups = []
    for v, n in sorted(solid.items(), key=lambda kv: -kv[1]):
        lab = oklab(parse_color(v))
        for g in groups:
            if math.dist(lab, g['lab']) < thr: g['members'].append((v, n)); g['n'] += n; g['alphas'] |= alphas[v]; break
        else: groups.append({'lead': v, 'lab': lab, 'members': [(v, n)], 'n': n, 'alphas': set(alphas[v])})
    return groups

def chroma(lab): return math.hypot(lab[1], lab[2])
def hue(lab): return (math.degrees(math.atan2(lab[2], lab[1])) + 360) % 360
def hue_name(h):
    for lim, name in ((42, 'red'), (68, 'orange'), (88, 'amber'), (115, 'yellow'), (175, 'green'), (225, 'cyan'), (278, 'blue'), (312, 'violet'), (355, 'pink'), (361, 'red')):   # OKLab hue bands
        if h < lim: return name

TYPE_SCALE = [11, 12, 13, 14, 15, 16, 18, 20, 24, 28, 32, 36, 40, 48, 56, 64, 72, 96]
RADIUS_SCALE = [0, 2, 4, 6, 8, 10, 12, 16, 20, 24, 28, 32, 9999]
SPACE_SCALE = [0, 1, 2, 4, 6, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128, 160]
snap = lambda v, scale: min(scale, key=lambda s: abs(s - v))
LIMITS = {'colors (distinct after grouping)': 20, 'near-duplicate colour groups': 2, 'opacity steps (worst colour)': 6, 'font families': 3, 'font sizes': 10, 'font weights': 4,
          'radii': 6, 'shadows': 5, 'z-index values': 8, 'breakpoints': 5, 'durations': 5, 'off-grid spacing (%)': 15, 'tailwind arbitrary values': 25}

def analyse(D, F, stats):
    col = {k: v for k, v in D['color'].items()}
    groups = color_groups(collections.Counter(col))
    dupes = [g for g in groups if len(g['members']) > 1]
    sizes = collections.Counter({k: v for k, v in D['size'].items() if 6 <= k <= 200})
    space = collections.Counter({k: v for k, v in D['space'].items() if k <= 400})
    off = sum(n for v, n in space.items() if v % 4 and v not in (1, 2, 6, 10, 14)) / max(1, sum(space.values())) * 100
    radii = collections.Counter()
    for k, v in D['radius'].items(): radii['full' if isinstance(k, (int, float)) and k >= 500 else k] += v
    fam = collections.Counter({k: v for k, v in D['family'].items() if k.lower() not in ('inherit', 'initial', 'unset')})
    fam_all = fam + collections.Counter({'tw:' + k: v for k, v in D['tw-font'].items()})
    weights = D['weight'] + collections.Counter({{'thin': '100', 'extralight': '200', 'light': '300', 'normal': '400', 'medium': '500', 'semibold': '600', 'bold': '700', 'extrabold': '800', 'black': '900'}[k]: v for k, v in D['tw-weight'].items()})
    measured = {'colors (distinct after grouping)': len(groups), 'near-duplicate colour groups': len(dupes), 'opacity steps (worst colour)': max([len(g['alphas']) for g in groups] or [0]), 'font families': len(fam_all),
                'font sizes': len(sizes) + len(D['tw-size']), 'font weights': len(weights), 'radii': len(radii) + len(D['tw-radius']),
                'shadows': len(D['shadow']) + len(D['tw-shadow']), 'z-index values': len(D['z-index']), 'breakpoints': len(D['breakpoint']),
                'durations': len(D['duration']), 'off-grid spacing (%)': round(off, 1), 'tailwind arbitrary values': sum(D['tw-arbitrary'].values())}
    over = {k: v for k, v in measured.items() if v > LIMITS[k]}
    raw_colors = sum(D['color'].values()) + sum(D['tw-arbitrary-color'].values())
    token_ratio = stats['var_uses'] / max(1, stats['var_uses'] + raw_colors)
    return dict(groups=groups, dupes=dupes, sizes=sizes, space=space, radii=radii, fam=fam_all, weights=weights, measured=measured, over=over,
                token_ratio=token_ratio, raw_colors=raw_colors)

def top(counter, n=14, fmt=str): return ', '.join(f'{fmt(k)} ×{v}' for k, v in counter.most_common(n)) or '—'

def report(root, D, F, stats, A):
    L = [f'# Design-system audit — `{os.path.basename(os.path.abspath(root))}`', '',
         f'{stats["files"]} source files scanned · {A["raw_colors"]} raw colour values · {stats["var_uses"]} `var(--…)` uses '
         f'({A["token_ratio"] * 100:.0f} % of colour references go through tokens) · {stats["inline_styles"]} inline style objects · '
         f'{len(D["css-var"])} CSS custom properties defined.', '']
    verdict = 'CONSOLIDATE' if len(A['over']) >= 3 else 'TIDY' if A['over'] else 'HEALTHY'
    L += ['## Verdict', '', {'CONSOLIDATE': f'**Consolidation recommended.** {len(A["over"])} of {len(LIMITS)} categories are over their healthy limit. Propose a merged design system on a new branch (SKILL.md, step 3).',
                             'TIDY': '**Mostly consistent.** Fix the categories over their limit inside the layer passes; a full design-system merge is optional.',
                             'HEALTHY': '**Healthy system.** Keep its tokens and redesign through them.'}[verdict], '']
    L += ['| Category | Found | Healthy limit | |', '|---|---|---|---|'] + [f'| {k} | {v} | ≤ {LIMITS[k]} | {"over" if k in A["over"] else "ok"} |' for k, v in A['measured'].items()] + ['']
    L += ['## Colour', '', f'{len(A["groups"])} distinct colours after grouping near-identical values (OKLab distance < 0.035).', '']
    chrom = [g for g in A['groups'] if chroma(g['lab']) > .04]; neutral = [g for g in A['groups'] if chroma(g['lab']) <= .04]
    fam = collections.Counter(hue_name(hue(g['lab'])) for g in chrom)
    L += [f'- Neutrals: {len(neutral)} · chromatic: {len(chrom)} across hue families {dict(fam.most_common())}.',
          f'- Most used: {top(collections.Counter({g["lead"]: g["n"] for g in A["groups"]}), 12)}']
    if A['dupes']:
        L += ['', '**Near-duplicates** (same colour typed differently — each group should become one token):', '']
        for g in sorted(A['dupes'], key=lambda g: -g['n'])[:15]: L.append(f'- `{g["lead"]}` ← ' + ', '.join(f'`{v}` ×{n}' for v, n in g['members'][1:]))
    many = sorted([g for g in A['groups'] if len(g['alphas']) > 4], key=lambda g: -len(g['alphas']))
    if many:
        L += ['', '**Opacity sprawl** (keep 3–4 alpha steps per colour, as tokens):', '']
        L += [f'- `{g["lead"]}` at {len(g["alphas"])} opacities: ' + ', '.join(sorted(g['alphas'], key=float)[:16]) for g in many[:8]]
    if D['tw-color']: L += ['', f'- Tailwind palette colours: {top(D["tw-color"], 16)}']
    L += ['', '## Type', '', f'- Families: {top(A["fam"], 8)}', f'- Sizes (px): {top(A["sizes"], 18, lambda v: "%g" % v)}']
    if D['tw-size']: L.append(f'- Tailwind sizes: {top(D["tw-size"], 12)}')
    L += [f'- Weights: {top(A["weights"], 9)}', f'- Line heights: {top(D["line-height"], 10)}', f'- Letter spacing: {top(D["letter-spacing"], 10)}', '']
    L += ['## Shape, space, depth', '', f'- Radii (px): {top(A["radii"], 14, lambda v: "%g" % v if isinstance(v, (int, float)) else v)}']
    if D['tw-radius']: L.append(f'- Tailwind radii: {top(D["tw-radius"], 10)}')
    L += [f'- Spacing (px): {top(A["space"], 18, lambda v: "%g" % v)} — {A["measured"]["off-grid spacing (%)"]} % off the 4-pt grid']
    if D['tw-space']: L.append(f'- Tailwind spacing steps: {top(D["tw-space"], 16)}')
    L += [f'- Shadows: {len(D["shadow"])} distinct raw values' + (f'; Tailwind {top(D["tw-shadow"], 8)}' if D['tw-shadow'] else '')]
    for s, n in D['shadow'].most_common(6): L.append(f'  - `{s}` ×{n}')
    L += [f'- z-index: {top(D["z-index"], 12)}', f'- Breakpoints (px): {top(D["breakpoint"], 10)}', f'- Durations (ms): {top(D["duration"], 10)}', '']
    if D['tw-arbitrary']: L += ['## Tailwind arbitrary values', '', top(D['tw-arbitrary'], 30), '']
    L += ['## Where the drift lives', '', 'Files with the most raw colour values (start the token migration here):', '']
    per_file = collections.Counter()
    for v, fs in F['color'].items():
        for f in fs: per_file[f] += 1
    L += [f'- `{f}` — {n} distinct colours' for f, n in per_file.most_common(10)] + ['']
    return '\n'.join(L)

def propose(A):
    """A first token proposal: one token per colour group, snapped type/radius/space scales, and the legacy → token map."""
    L = ['# Design-system proposal (draft — review before applying)', '',
         'Generated by `audit.py --propose`. Names are suggestions; the mapping is what matters: every legacy value on the left becomes the token on the right.', '']
    neutral = [g for g in A['groups'] if chroma(g['lab']) <= .04]
    chrom = sorted([g for g in A['groups'] if chroma(g['lab']) > .04], key=lambda g: -g['n'])
    # one 11-step neutral ramp at fixed OKLab lightness, tinted like the project's own greys (usage-weighted)
    RAMP = [(50, .985), (100, .967), (200, .922), (300, .87), (400, .708), (500, .556), (600, .439), (700, .371), (800, .269), (900, .205), (950, .145)]
    w = sum(g['n'] for g in neutral) or 1; ta = sum(g['lab'][1] * g['n'] for g in neutral) / w; tb = sum(g['lab'][2] * g['n'] for g in neutral) / w
    L += ['## Colour', '', f'### Neutral ramp ({len(neutral)} greys today → 11 steps, plus white and black)', '',
          'Steps sit at fixed OKLab lightness and carry the average tint of the greys the project already uses.', '', '| Token | Value | Replaces |', '|---|---|---|']
    slots = collections.defaultdict(list)
    for g in neutral:
        if g['lab'][0] > .995: slots['white'].append(g); continue
        if g['lab'][0] < .02: slots['black'].append(g); continue
        st = min(RAMP, key=lambda r: abs(r[1] - g['lab'][0]))[0]; slots[st].append(g)
    rows = [('white', '#ffffff')] + [(st, hexstr(oklab2rgb(l, ta * min(1, l / .5), tb * min(1, l / .5)))) for st, l in RAMP] + [('black', '#000000')]
    for st, val in rows:
        name = f'--{st}' if st in ('white', 'black') else f'--gray-{st}'
        reps = ', '.join(f'`{v}`' for g in slots.get(st, []) for v, _ in g['members']) or '—'
        L.append(f'| `{name}` | `{val}` | {reps} |')
    L += ['', '### Brand and state colours, by hue family (most used first)', '',
          'Keep one colour per role. The most used family is usually the brand accent; red, green and amber become `--danger`, `--success` and `--warning`. Extra shades in a family become ramp steps or go.', '',
          '| Family | Keep | Uses | Also in this family (merge or drop) |', '|---|---|---|---|']
    fams = collections.OrderedDict()
    for g in chrom: fams.setdefault(hue_name(hue(g['lab'])), []).append(g)
    for f, gs in fams.items():
        L.append(f'| {f} | `{gs[0]["lead"]}` | {sum(g["n"] for g in gs)} | ' + (', '.join(f'`{v}`' for g in gs for v, _ in g['members'] if v != gs[0]['lead']) or '—') + ' |')
    L += ['', 'Then add the **semantic layer** on top (what components use): `--bg`, `--surface`, `--text`, `--text-muted`, `--border`, `--accent`, `--accent-text`, `--success`, `--warning`, `--danger`, `--focus`. Components never read a primitive directly.', '']
    def scale_table(title, counter, scale, unit='px'):
        m = collections.defaultdict(list)
        for v, n in counter.items():
            if isinstance(v, (int, float)): m[snap(v, scale)].append((v, n))
            elif v == 'full': m[9999].append((9999, n))
        out = [f'## {title}', '', '| Token value | Replaces (uses) |', '|---|---|']
        for k in sorted(m): out.append(f'| {"full" if k == 9999 else "%g%s" % (k, unit)} | ' + ', '.join(f'{"%g" % v} ×{n}' for v, n in sorted(m[k])) + ' |')
        return out + ['']
    L += scale_table('Type scale', A['sizes'], TYPE_SCALE) + scale_table('Radius', A['radii'], RADIUS_SCALE) + scale_table('Spacing (4-pt grid)', A['space'], SPACE_SCALE)
    L += ['## Next', '', '1. Keep the 6–8 type steps the product really needs, 3–4 radii, 2–3 shadows; drop the rest.',
          '2. Write the tokens file (see `references/design-system.md` for Tailwind, CSS variables, shadcn, React Native, SwiftUI and Flutter formats).',
          '3. Alias the old names to the new tokens so nothing breaks, then migrate file by file, starting with the files listed at the end of the audit.']
    return '\n'.join(L)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('root'); ap.add_argument('--out'); ap.add_argument('--json'); ap.add_argument('--propose')
    a = ap.parse_args()
    if not os.path.isdir(a.root): sys.exit(f'not a directory: {a.root}')
    D, F, stats = scan(a.root)
    if not stats['files']: sys.exit('no source files found (looked for ' + ' '.join(sorted(EXTS)) + ')')
    A = analyse(D, F, stats); md = report(a.root, D, F, stats, A)
    if a.out: open(a.out, 'w').write(md + '\n'); print(f'wrote {a.out}')
    else: print(md)
    if a.json:
        json.dump({'stats': dict(stats), 'measured': A['measured'], 'over': A['over'], 'token_ratio': A['token_ratio'],
                   'colors': [{'lead': g['lead'], 'uses': g['n'], 'members': g['members']} for g in A['groups']],
                   'values': {k: {str(x): n for x, n in v.most_common()} for k, v in D.items()}}, open(a.json, 'w'), indent=1)
        print(f'wrote {a.json}')
    if a.propose: open(a.propose, 'w').write(propose(A) + '\n'); print(f'wrote {a.propose}')

if __name__ == '__main__':
    main()
