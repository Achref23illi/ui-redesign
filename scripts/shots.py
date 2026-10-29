#!/usr/bin/env python3
"""shots.py — screenshot every route of a running app at phone and desktop widths, then build contact sheets.
Use it before the first change (the "before" set) and after every layer (the "after" sets), and judge the sheets.

  python3 scripts/shots.py http://localhost:3000 / /pricing /dashboard --out shots/before
  python3 scripts/shots.py http://localhost:3000 --routes routes.txt --out shots/after-type --widths 390,1440
  python3 scripts/shots.py --compare shots/before shots/after-type --out shots/compare   # side-by-side pairs

Needs Playwright (pip install playwright && playwright install chromium) and Pillow for sheets/compare.
"""
import argparse, os, re, sys

def slug(route): return re.sub(r'[^\w-]+', '_', route.strip('/')) or 'home'

def capture(base, routes, out, widths, full, wait):
    from playwright.sync_api import sync_playwright
    os.makedirs(out, exist_ok=True)
    with sync_playwright() as p:
        try: b = p.chromium.launch()
        except Exception: b = p.chromium.launch(channel='chrome')      # no bundled Chromium: use the installed Chrome
        for w in widths:
            ctx = b.new_context(viewport={'width': w, 'height': 844 if w < 600 else 900}, device_scale_factor=2 if w < 600 else 1,
                                is_mobile=w < 600, has_touch=w < 600, reduced_motion='reduce')
            pg = ctx.new_page()
            for r in routes:
                url = base.rstrip('/') + '/' + r.lstrip('/')
                try:
                    pg.goto(url, wait_until='networkidle', timeout=45000)
                except Exception as e:
                    print('skip', url, '·', str(e).splitlines()[0]); continue
                pg.wait_for_timeout(wait)
                path = os.path.join(out, f'{w:04d}-{slug(r)}.png'); pg.screenshot(path=path, full_page=full); print('shot', path)
            ctx.close()
        b.close()

def sheet(folder, cols=3, tw=420):
    from PIL import Image, ImageDraw
    fs = sorted(f for f in os.listdir(folder) if f.endswith('.png') and not f.startswith('sheet'))
    groups = {}
    for f in fs: groups.setdefault(f.split('-')[0], []).append(f)
    for w, items in groups.items():
        for k in range(0, len(items), cols * 2):
            chunk = items[k:k + cols * 2]; ims = []
            for f in chunk:
                im = Image.open(os.path.join(folder, f)).convert('RGB'); h = int(im.height * tw / im.width); ims.append((f, im.resize((tw, h))))
            th = min(max(i.height for _, i in ims), 1400); rows = (len(ims) + cols - 1) // cols
            S = Image.new('RGB', (cols * (tw + 16) + 16, rows * (th + 40) + 16), (24, 24, 26)); d = ImageDraw.Draw(S)
            for n, (f, im) in enumerate(ims):
                x, y = 16 + (n % cols) * (tw + 16), 16 + (n // cols) * (th + 40)
                S.paste(im.crop((0, 0, tw, min(th, im.height))), (x, y + 24)); d.text((x, y + 4), f, fill=(230, 230, 230))
            out = os.path.join(folder, f'sheet-{w}-{k // (cols * 2) + 1}.jpg'); S.save(out, quality=85); print('sheet', out)

def compare(a, b, out, tw=420):
    from PIL import Image, ImageDraw
    os.makedirs(out, exist_ok=True)
    for f in sorted(set(os.listdir(a)) & set(os.listdir(b))):
        if not f.endswith('.png'): continue
        A, B = (Image.open(os.path.join(d, f)).convert('RGB') for d in (a, b))
        A, B = (i.resize((tw, int(i.height * tw / i.width))) for i in (A, B)); h = min(max(A.height, B.height), 1600)
        S = Image.new('RGB', (tw * 2 + 48, h + 40), (24, 24, 26)); d = ImageDraw.Draw(S)
        S.paste(A.crop((0, 0, tw, min(h, A.height))), (16, 32)); S.paste(B.crop((0, 0, tw, min(h, B.height))), (tw + 32, 32))
        d.text((16, 10), 'before · ' + f, fill=(200, 200, 200)); d.text((tw + 32, 10), 'after', fill=(200, 200, 200))
        p = os.path.join(out, f.replace('.png', '.jpg')); S.save(p, quality=85); print('pair', p)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('base', nargs='?'); ap.add_argument('routes', nargs='*')
    ap.add_argument('--routes', dest='routes_file'); ap.add_argument('--out', default='shots/current')
    ap.add_argument('--widths', default='390,1440'); ap.add_argument('--full', action='store_true', help='full-page screenshots')
    ap.add_argument('--wait', type=int, default=600, help='ms to wait after load'); ap.add_argument('--compare', nargs=2, metavar=('BEFORE', 'AFTER'))
    a = ap.parse_args()
    if a.compare: compare(*a.compare, a.out); return
    if not a.base: sys.exit('give the base URL of the running app, e.g. http://localhost:3000')
    routes = list(a.routes) or ['/']
    if a.routes_file: routes += [l.strip() for l in open(a.routes_file) if l.strip() and not l.startswith('#')]
    capture(a.base, routes, a.out, [int(w) for w in a.widths.split(',')], a.full, a.wait)
    try: sheet(a.out)
    except ImportError: print('Pillow not installed: skipped contact sheets')

if __name__ == '__main__':
    main()
