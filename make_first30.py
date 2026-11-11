import math, os
import numpy as np

OUT = os.path.dirname(os.path.abspath(__file__))
L = 9.81
BMAX = 1.60

def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))

def dist(a, b):
    return math.dist(a, b)

def profile(ctrl, xq, n=60):
    pts = [np.array(p, float) for p in ctrl]
    ext = [2 * pts[0] - pts[1]] + pts + [2 * pts[-1] - pts[-2]]
    xs, ys = [], []
    for i in range(len(ext) - 3):
        p0, p1, p2, p3 = ext[i:i + 4]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            p = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            xs.append(p[0]); ys.append(p[1])
    xs.append(ext[-1][0]); ys.append(ext[-1][1])
    return np.interp(xq, xs, ys)

beam_ctrl = [(0, 1.02), (1.5, 1.44), (3.0, 1.58), (4.6, 1.60), (6.5, 1.56), (8.2, 1.28), (9.2, 0.62), (9.81, 0.10)]
sheer_ctrl = [(0, 0.92), (2.5, 0.82), (5.5, 0.78), (7.5, 0.86), (8.8, 1.08), (9.81, 1.34)]
bot_ctrl = [(0, -0.10), (1.5, -0.38), (3.5, -0.58), (4.8, -0.62), (6.5, -0.56), (8.3, -0.44), (9.4, -0.30), (9.81, -0.24)]

xs = np.linspace(0, L, 26)
bb = profile(beam_ctrl, xs)
zs = profile(sheer_ctrl, xs)
zb = profile(bot_ctrl, xs)

def section(x, b_, ztop, zbot, n=12):
    w = min(1.0, max(0.0, (7.6 - x) / 2.6))
    vc = 1.0 - 0.45 * w
    yc = 0.93 * b_ * w
    zc = zbot + 0.42 * w * (ztop - zbot)
    pts = []
    N = 2 * n + 1
    for k in range(N):
        s = k / (N - 1)
        v = 1.0 - abs(2 * s - 1.0)
        if v <= vc:
            t = v / vc
            y = b_ + (yc - b_) * t + 0.02 * b_ * math.sin(math.pi * t) * w
            z = ztop + (zc - ztop) * (t ** 0.9)
        else:
            t = (v - vc) / (1 - vc)
            y = yc * math.sin(0.5 * math.pi * (1 - t)) ** 0.75
            z = zc + (zbot - zc) * t
        if s > 0.5:
            y = -y
        pts.append((x, y, z))
    return pts

def stitch(A, B):
    if dist(A[0], B[-1]) < dist(A[0], B[0]):
        B = B[::-1]
    faces = []
    i = j = 0
    n, m = len(A), len(B)
    while i < n - 1 or j < m - 1:
        if i == n - 1:
            faces.append((A[i], B[j], B[j + 1])); j += 1
        elif j == m - 1:
            faces.append((A[i], A[i + 1], B[j])); i += 1
        else:
            da = dist(A[i], A[i + 1]); db = dist(B[j], B[j + 1])
            if da <= db:
                faces.append((A[i], A[i + 1], B[j])); i += 1
            else:
                faces.append((A[i], B[j + 1], B[j])); j += 1
    return faces

def fan(pts):
    return [(pts[0], pts[i], pts[i + 1]) for i in range(1, len(pts) - 1)]

def box(x0, x1, y0, y1, z0, z1):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return v, f

def foil(zlist, le, te, th, n=8):
    verts, faces = [], []
    ring = []
    for z, l, t, thk in zip(zlist, le, te, th):
        c = t - l
        ring = []
        for i in range(n + 1):
            u = i / n
            ring.append((l + u * c, 0.5 * thk * math.sin(math.pi * u) ** 0.75, z))
        for i in range(n - 1, 0, -1):
            u = i / n
            ring.append((l + u * c, -0.5 * thk * math.sin(math.pi * u) ** 0.75, z))
        verts += ring
    m = len(ring)
    for k in range(len(zlist) - 1):
        for i in range(m - 1):
            faces.append((k * m + i, k * m + i + 1, (k + 1) * m + i + 1, (k + 1) * m + i))
    faces.append(tuple(range(0, m)))
    base = (len(zlist) - 1) * m
    faces.append(tuple(range(base, base + m)))
    return verts, faces

def ellipsoid(c, r, nu=12, nv=10):
    verts, faces = [], []
    for i in range(nu + 1):
        u = i / nu * math.pi
        for j in range(nv + 1):
            v = j / nv * 2 * math.pi
            verts.append((c[0] + r[0] * math.sin(u) * math.cos(v), c[1] + r[1] * math.sin(u) * math.sin(v), c[2] + r[2] * math.cos(u)))
    for i in range(nu):
        for j in range(nv):
            faces.append((i * (nv + 1) + j, i * (nv + 1) + j + 1, (i + 1) * (nv + 1) + j + 1, (i + 1) * (nv + 1) + j))
    return verts, faces

def cylinder(p0, p1, r, n=10):
    p0 = np.array(p0, float); p1 = np.array(p1, float)
    ax = p1 - p0
    ax = ax / np.linalg.norm(ax)
    tmp = np.array([0, 0, 1.0]) if abs(ax[2]) < 0.9 else np.array([1.0, 0, 0])
    u = np.cross(ax, tmp); u /= np.linalg.norm(u)
    v = np.cross(ax, u)
    verts, faces = [], []
    for p in (p0, p1):
        for i in range(n):
            a = 2 * math.pi * i / n
            verts.append(tuple(p + r * (math.cos(a) * u + math.sin(a) * v)))
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n + j, n + i))
    faces.append(tuple(range(n - 1, -1, -1)))
    faces.append(tuple(range(n, 2 * n)))
    return verts, faces

def wheel(c, R=0.33, r=0.028, tilt=math.radians(18), n=20, m=6):
    e1 = np.array([math.sin(tilt), 0, math.cos(tilt)])
    e2 = np.array([0, 1, 0])
    ex = np.array([1.0, 0, 0])
    c = np.array(c, float)
    verts, faces = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        P = c + R * (math.cos(a) * e1 + math.sin(a) * e2)
        n1 = -math.sin(a) * e1 + math.cos(a) * e2
        for j in range(m):
            b = 2 * math.pi * j / m
            verts.append(tuple(P + r * (math.cos(b) * n1 + math.sin(b) * ex)))
    for i in range(n):
        i2 = (i + 1) % n
        for j in range(m):
            j2 = (j + 1) % m
            faces.append((i * m + j, i2 * m + j, i2 * m + j2, i * m + j2))
    spokes = []
    hub = tuple(c)
    for k in range(5):
        a = 2 * math.pi * k / 5
        rim = tuple(c + R * (math.cos(a) * e1 + math.sin(a) * e2))
        spokes.append([hub, rim])
    return verts, faces, spokes

def grid_mesh(A, B, m=8, amp=0.16):
    n = len(A) - 1
    verts, faces = [], []
    for i in range(n + 1):
        s = i / n
        for j in range(m + 1):
            u = j / m
            p = lerp3(A[i], B[i], u)
            verts.append((p[0], p[1] + amp * math.sin(math.pi * u) * (0.35 + 0.65 * s), p[2]))
    for i in range(n):
        for j in range(m):
            a = i * (m + 1) + j
            faces.append((a, a + 1, a + (m + 1) + 1, a + (m + 1)))
    return verts, faces

G = {}
def newg(name, mtl):
    G[name] = {'v': [], 'f': [], 'l': [], 'mtl': mtl}

def add_mesh(name, verts, faces):
    g = G[name]
    off = len(g['v'])
    g['v'] += [tuple(map(float, p)) for p in verts]
    g['f'] += [tuple(i + off for i in f) for f in faces]

def add_pts(name, pts, lines):
    g = G[name]
    for poly in lines:
        idx = []
        for p in poly:
            g['v'].append(tuple(map(float, p)))
            idx.append(len(g['v']) - 1)
        g['l'].append(idx)

newg('Hull', 'Hull')
rings = [section(x, bb[i], zs[i], zb[i]) for i, x in enumerate(xs)]
hv, hf = [], []
for r in rings:
    off = len(hv); hv += r
    if hf or True:
        pass
faces_raw = []
for i in range(len(rings) - 1):
    faces_raw += stitch(rings[i], rings[i + 1])
faces_raw += fan(rings[0]) + fan(rings[-1])
add_mesh('Hull', hv, [tuple(hv.index(p) if False else 0 for _ in f) for f in faces_raw[:0]])

G['Hull']['v'] = []
G['Hull']['f'] = []
idxmap = {}
hv = []
for r in rings:
    base = len(hv)
    idxmap[id(r)] = [base + k for k in range(len(r))]
    hv += r
allf = []
for i in range(len(rings) - 1):
    for f in stitch(rings[i], rings[i + 1]):
        allf.append(tuple(idxmap[id(rings[i])][rings[i].index(f[0])] for f in [f]))
allf = []
for i in range(len(rings) - 1):
    ia = idxmap[id(rings[i])]; ib = idxmap[id(rings[i + 1])]
    for f in stitch(rings[i], rings[i + 1]):
        idx = []
        for p in f:
            if p in rings[i]:
                idx.append(ia[rings[i].index(p)])
            else:
                idx.append(ib[rings[i + 1].index(p)])
        allf.append(tuple(idx))
for f in fan(rings[0]):
    allf.append(tuple(idxmap[id(rings[0])][rings[0].index(p)] for p in f))
for f in fan(rings[-1]):
    allf.append(tuple(idxmap[id(rings[-1])][rings[-1].index(p)] for p in f))
add_mesh('Hull', hv, allf)

newg('Stripe', 'Stripe')
sv, sf = [], []
zlo, zhi = 0.03, 0.12
def side_pt(ring, zt, stbd):
    half = ring[:len(ring) // 2 + 1] if stbd else ring[len(ring) // 2:]
    for a, b2 in zip(half, half[1:]):
        if (a[2] - zt) * (b2[2] - zt) <= 0 and a[2] != b2[2]:
            t = (zt - a[2]) / (b2[2] - a[2])
            return (a[0], a[1] + (b2[1] - a[1]) * t, zt)
    return None
low = [[side_pt(r, zlo, True), side_pt(r, zlo, False)] for r in rings]
high = [[side_pt(r, zhi, True), side_pt(r, zhi, False)] for r in rings]
for i in range(len(rings) - 1):
    for side in (0, 1):
        p = [low[i][side], high[i][side], high[i + 1][side], low[i + 1][side]]
        if None in p:
            continue
        base = len(sv); sv += p
        sf.append((base, base + 1, base + 2, base + 3))
add_mesh('Stripe', sv, sf)

newg('Deck', 'Deck')
def dz_at(x, y):
    b_ = float(np.interp(x, xs, bb)); t = float(np.interp(x, xs, zs))
    return t + 0.06 * (1 - (y / b_) ** 2)
deck_rings = []
for i, x in enumerate(xs):
    if 0.78 <= x <= 4.06:
        yc = 1.00 + 0.08 * math.sin(math.pi * (x - 0.78) / (4.06 - 0.78))
        zf = float(zs[i]) - 0.38
        pts = [(x, y, dz_at(x, y)) for y in np.linspace(bb[i], yc, 4)]
        pts.append((x, yc, zf))
        pts += [(x, y, zf) for y in np.linspace(yc, -yc, 7)]
        pts.append((x, -yc, float(zs[i]) + 0.02))
        pts += [(x, y, dz_at(x, y)) for y in np.linspace(-yc, -bb[i], 4)]
    else:
        pts = [(x, y, dz_at(x, y)) for y in np.linspace(bb[i], -bb[i], 9)]
    deck_rings.append(pts)
dv, df = [], []
imap = {}
for r in deck_rings:
    base = len(dv); imap[id(r)] = list(range(base, base + len(r)))
    dv += r
for i in range(len(deck_rings) - 1):
    ia = imap[id(deck_rings[i])]; ib = imap[id(deck_rings[i + 1])]
    for f in stitch(deck_rings[i], deck_rings[i + 1]):
        idx = []
        for p in f:
            if p in deck_rings[i]:
                idx.append(ia[deck_rings[i].index(p)])
            else:
                idx.append(ib[deck_rings[i + 1].index(p)])
        df.append(tuple(idx))
add_mesh('Deck', dv, df)

newg('Benches', 'Cockpit')
bv, bf = [], []
for sgn in (1, -1):
    x0, x1 = 1.0, 3.85
    y0, y1 = sgn * 0.45, sgn * 0.98
    zm = float(np.interp((x0 + x1) / 2, xs, zs)) - 0.38
    v, f = box(x0, x1, min(y0, y1), max(y0, y1), zm, zm + 0.18)
    base = len(bv); bv += v; bf += [tuple(i + base for i in fc) for fc in f]
add_mesh('Benches', bv, bf)

newg('Coachroof', 'Coachroof')
cx = [4.15, 4.5, 5.0, 5.45, 5.7]
wc = [0.06, 0.55, 0.62, 0.60, 0.32]
h = 0.30
crings = []
for x, w in zip(cx, wc):
    pts = [(x, -w, dz_at(x, -w)), (x, -0.98 * w, dz_at(x, -0.98 * w) + 0.55 * h), (x, -0.6 * w, dz_at(x, -0.6 * w) + 0.9 * h),
           (x, 0, float(np.interp(x, xs, zs)) + 0.06 + h), (x, 0.6 * w, dz_at(x, 0.6 * w) + 0.9 * h),
           (x, 0.98 * w, dz_at(x, 0.98 * w) + 0.55 * h), (x, w, dz_at(x, w))]
    crings.append(pts)
cv, cf = [], []
cmap = {}
for r in crings:
    base = len(cv); cmap[id(r)] = list(range(base, base + len(r)))
    cv += r
for i in range(len(crings) - 1):
    ia = cmap[id(crings[i])]; ib = cmap[id(crings[i + 1])]
    for f in stitch(crings[i], crings[i + 1]):
        idx = []
        for p in f:
            if p in crings[i]:
                idx.append(ia[crings[i].index(p)])
            else:
                idx.append(ib[crings[i + 1].index(p)])
        cf.append(tuple(idx))
for r in (crings[0], crings[-1]):
    base = cmap[id(r)]
    for k in range(1, len(r) - 1):
        cf.append((base[0], base[k], base[k + 1]))
add_mesh('Coachroof', cv, cf)

newg('Windows', 'Windows')
wv, wf = [], []
for sgn in (1, -1):
    for x1, x2 in [(4.55, 5.15), (5.22, 5.62)]:
        xm = (x1 + x2) / 2
        w = float(np.interp(xm, cx, wc))
        y = sgn * (w + 0.015)
        z1 = dz_at(xm, w) + 0.10
        z2 = dz_at(xm, w) + 0.23
        base = len(wv)
        wv += [(x1, y, z1), (x2, y, z1), (x2, y, z2), (x1, y, z2)]
        wf.append((base, base + 1, base + 2, base + 3))
add_mesh('Windows', wv, wf)

newg('Hatch', 'Hatch')
hv2 = [(7.4, -0.5, dz_at(7.4, -0.5) + 0.05), (8.5, -0.5, dz_at(8.5, -0.5) + 0.05), (8.5, 0.5, dz_at(8.5, 0.5) + 0.05), (7.4, 0.5, dz_at(7.4, 0.5) + 0.05)]
add_mesh('Hatch', hv2, [(0, 1, 2, 3)])

newg('Keel', 'Keel')
kz = [-0.50, -0.9, -1.3, -1.6, -1.78]
add_mesh('Keel', *foil(kz, [4.45, 4.55, 4.65, 4.72, 4.78], [5.45, 5.35, 5.25, 5.15, 5.05], [0.10, 0.11, 0.11, 0.10, 0.08]))

newg('Bulb', 'Bulb')
add_mesh('Bulb', *ellipsoid((4.90, 0, -1.80), (0.42, 0.16, 0.10)))

newg('Rudders', 'Keel')
for sgn in (1, -1):
    v, f = foil([-0.15, -0.6, -1.0, -1.45], [0.30, 0.34, 0.38, 0.42], [0.88, 0.82, 0.75, 0.68], [0.05, 0.055, 0.05, 0.04])
    v = [(p[0], p[1] + sgn * 0.70, p[2]) for p in v]
    add_mesh('Rudders', v, f)

xm = 5.9
zdeck_m = float(np.interp(xm, xs, zs)) + 0.06
ztop = zdeck_m + 13.0
zboom = zdeck_m + 1.15
zhead = zdeck_m + 0.86 * 13.0

newg('Mast', 'Alu')
add_mesh('Mast', *cylinder((xm, 0, zdeck_m - 0.3), (xm, 0, ztop), 0.065, 10))
newg('Boom', 'Alu')
add_mesh('Boom', *cylinder((xm, 0, zboom), (xm - 4.3, 0, zboom + 0.02), 0.05, 8))
newg('Sprit', 'Alu')
add_mesh('Sprit', *cylinder((9.70, 0, 1.30), (11.05, 0, 1.80), 0.045, 8))

newg('Mainsail', 'Sail')
n = 10
A, B = [], []
for i in range(n + 1):
    s = i / n
    A.append(lerp3((xm, 0, zboom), (xm, 0, zhead), s))
    p = lerp3((xm - 4.3, 0, zboom + 0.06), (xm, 0, zhead), s)
    B.append((p[0] - 0.42 * math.sin(math.pi * s), p[1], p[2]))
add_mesh('Mainsail', *grid_mesh(A, B, m=8, amp=0.16))

newg('Jib', 'Sail')
F = (xm, 0, ztop * 0.985)
Tk = (9.35, 0, 1.26)
Cl = (7.7, 0, 1.10)
A, B = [], []
for i in range(n + 1):
    s = i / n
    A.append(lerp3(Tk, F, s))
    p = lerp3(Cl, F, s)
    B.append((p[0] - 0.18 * math.sin(math.pi * s), p[1], p[2]))
add_mesh('Jib', *grid_mesh(A, B, m=8, amp=0.12))

newg('Rigging', 'Steel')
add_pts('Rigging', None, [
    [(11.05, 0, 1.80), (xm, 0, ztop * 0.985)],
    [(xm, 0, ztop), (0.12, 0, 0.95)],
    [(xm, 0, 12.6), (5.15, 1.58, 0.90)],
    [(xm, 0, 12.6), (5.15, -1.58, 0.90)],
    [(xm, 0, 8.6), (5.5, 1.60, 0.86)],
    [(xm, 0, 8.6), (5.5, -1.60, 0.86)],
    [(xm, 0, 13.2), (xm - 4.3, 0, zboom)],
    [(xm, 0, 8.7), (5.78, 0.62, 8.85)],
    [(xm, 0, 8.7), (5.78, -0.62, 8.85)],
])

newg('Railings', 'Alu')
rails = []
for sgn in (1, -1):
    xs_r = np.arange(0.5, 9.45, 0.9)
    tops = []
    mids = []
    for x in xs_r:
        b_ = float(np.interp(x, xs, bb)) * 0.985
        z0 = float(np.interp(x, xs, zs)) + 0.02
        rails.append([(x, sgn * b_, z0), (x, sgn * b_, z0 + 0.62)])
        tops.append((x, sgn * b_, z0 + 0.62))
        mids.append((x, sgn * b_, z0 + 0.33))
    rails.append(tops)
    rails.append(mids)
rails.append([(9.55, -0.28, dz_at(9.55, -0.28)), (9.55, -0.28, dz_at(9.55, -0.28) + 0.62)])
rails.append([(9.55, 0.28, dz_at(9.55, 0.28)), (9.55, 0.28, dz_at(9.55, 0.28) + 0.62)])
rails.append([(9.55, -0.28, dz_at(9.55, 0) + 0.64), (9.55, 0.28, dz_at(9.55, 0) + 0.64), (9.85, 0, 1.45)])
rails.append([(0.10, -0.92, dz_at(0.10, -0.92)), (0.10, -0.92, dz_at(0.10, -0.92) + 0.62)])
rails.append([(0.10, 0.92, dz_at(0.10, 0.92)), (0.10, 0.92, dz_at(0.10, 0.92) + 0.62)])
rails.append([(0.10, -0.92, dz_at(0.10, -0.92) + 0.62), (0.10, 0.92, dz_at(0.10, 0.92) + 0.62)])
add_pts('Railings', None, rails)

newg('Wheels', 'Dark')
for sgn in (1, -1):
    v, f, spokes = wheel((0.14, sgn * 0.55, 0.70), R=0.35)
    add_mesh('Wheels', v, f)
    add_pts('Wheels', None, spokes)
    add_mesh('Wheels', *cylinder((0.14, sgn * 0.55, 0.70), (0.14, sgn * 0.55, 0.50), 0.04, 8))

MTL = """newmtl Hull
Kd 0.95 0.96 0.98
Ka 0.2 0.2 0.2
Ks 0.4 0.4 0.45
Ns 60
newmtl Stripe
Kd 0.04 0.08 0.28
Ka 0.05 0.05 0.1
Ks 0.3 0.3 0.4
Ns 40
newmtl Deck
Kd 0.74 0.75 0.71
Ka 0.2 0.2 0.2
Ks 0.1 0.1 0.1
Ns 10
newmtl Cockpit
Kd 0.55 0.56 0.58
Ka 0.15 0.15 0.15
Ks 0.1 0.1 0.1
Ns 10
newmtl Coachroof
Kd 0.93 0.94 0.96
Ka 0.2 0.2 0.2
Ks 0.3 0.3 0.35
Ns 50
newmtl Windows
Kd 0.05 0.08 0.13
Ka 0.05 0.05 0.08
Ks 0.6 0.6 0.7
Ns 90
newmtl Hatch
Kd 0.22 0.23 0.26
Ka 0.1 0.1 0.1
Ks 0.2 0.2 0.2
Ns 20
newmtl Keel
Kd 0.14 0.15 0.18
Ka 0.05 0.05 0.06
Ks 0.2 0.2 0.2
Ns 15
newmtl Bulb
Kd 0.65 0.08 0.08
Ka 0.2 0.05 0.05
Ks 0.15 0.15 0.15
Ns 15
newmtl Alu
Kd 0.58 0.60 0.63
Ka 0.15 0.15 0.16
Ks 0.5 0.5 0.55
Ns 70
newmtl Sail
Kd 0.97 0.95 0.88
Ka 0.25 0.25 0.22
Ks 0.05 0.05 0.05
Ns 5
newmtl Steel
Kd 0.50 0.52 0.56
Ka 0.15 0.15 0.16
Ks 0.6 0.6 0.65
Ns 80
newmtl Dark
Kd 0.10 0.10 0.12
Ka 0.05 0.05 0.06
Ks 0.3 0.3 0.3
Ns 40
"""

obj_path = os.path.join(OUT, 'First30_JK.obj')
mtl_path = os.path.join(OUT, 'First30_JK.mtl')
with open(mtl_path, 'w') as f:
    f.write(MTL)
with open(obj_path, 'w') as f:
    f.write('# Voilier type Beneteau First 30 JK - modele 3D parametrique\n')
    f.write('# LOA 9.81 m, bau 3.20 m, tirant d eau 1.90 m\n')
    f.write('mtllib First30_JK.mtl\n')
    off = 0
    for name, g in G.items():
        f.write('o %s\nusemtl %s\n' % (name, g['mtl']))
        for v in g['v']:
            f.write('v %.4f %.4f %.4f\n' % v)
        for fc in g['f']:
            f.write('f ' + ' '.join(str(i + off + 1) for i in fc) + '\n')
        for ln in g['l']:
            f.write('l ' + ' '.join(str(i + off + 1) for i in ln) + '\n')
        off += len(g['v'])

def write_stl(path):
    with open(path, 'w') as f:
        f.write('solid First30_JK\n')
        for name, g in G.items():
            if not g['f']:
                continue
            for fc in g['f']:
                pts = [g['v'][i] for i in fc]
                if len(pts) == 3:
                    tris = [pts]
                else:
                    tris = [pts[:3], [pts[0], pts[2], pts[3]]]
                for t in tris:
                    a, b_, c = t
                    u = np.array(b_) - np.array(a)
                    v = np.array(c) - np.array(a)
                    nrm = np.cross(u, v)
                    ln = np.linalg.norm(nrm)
                    nrm = nrm / ln if ln > 0 else nrm
                    f.write(' facet normal %.5f %.5f %.5f\n  outer loop\n' % tuple(nrm))
                    for p in t:
                        f.write('   vertex %.4f %.4f %.4f\n' % p)
                    f.write('  endloop\n endfacet\n')
        f.write('endsolid First30_JK\n')

write_stl(os.path.join(OUT, 'First30_JK.stl'))

allv = [v for g in G.values() for v in g['v']]
arr = np.array(allv)
print('groupes:', len(G))
for name, g in G.items():
    print('  %-10s v=%4d f=%4d l=%2d' % (name, len(g['v']), len(g['f']), len(g['l'])))
print('total sommets:', len(allv), 'faces:', sum(len(g['f']) for g in G.values()))
print('bbox x: %.2f .. %.2f (longueur hors tout ~ %.2f m)' % (arr[:, 0].min(), arr[:, 0].max(), arr[:, 0].max() - arr[:, 0].min()))
print('bbox y: %.2f .. %.2f (bau ~ %.2f m)' % (arr[:, 1].min(), arr[:, 1].max(), arr[:, 1].max() - arr[:, 1].min()))
print('bbox z: %.2f .. %.2f (tirant eau ~ %.2f m, mat ~ %.2f m)' % (arr[:, 2].min(), arr[:, 2].max(), -arr[:, 2].min(), arr[:, 2].max()))
print('OBJ ecrit:', obj_path)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection

colors = {'Hull': '#f4f6f8', 'Stripe': '#0a1e4a', 'Deck': '#c9c7bd', 'Benches': '#8f9296', 'Coachroof': '#eef0f2',
          'Windows': '#101820', 'Hatch': '#3a3d42', 'Keel': '#23262b', 'Bulb': '#a51212', 'Rudders': '#23262b',
          'Mast': '#9aa0a6', 'Boom': '#9aa0a6', 'Sprit': '#9aa0a6', 'Mainsail': '#f7f3e8', 'Jib': '#f2ecdc',
          'Rigging': '#6d747c', 'Railings': '#b9bec4', 'Wheels': '#1c1e22'}

views = [('iso', 20, -58), ('side', 6, -90), ('front', 8, 2), ('top', 88, -90), ('stern', 14, 122)]
for name, elev, azim in views:
    fig = plt.figure(figsize=(12, 9), dpi=110)
    ax = fig.add_subplot(111, projection='3d')
    for gname, g in G.items():
        col = colors.get(gname, '#cccccc')
        if g['f']:
            pc = Poly3DCollection([ [g['v'][i] for i in fc] for fc in g['f'] ], facecolor=col, edgecolor='none', alpha=1.0)
            ax.add_collection3d(pc)
        if g['l']:
            segs = []
            for ln in g['l']:
                for a, b2 in zip(ln, ln[1:]):
                    segs.append([g['v'][a], g['v'][b2]])
            ax.add_collection3d(Line3DCollection(segs, colors=col, linewidths=1.0))
    water = Poly3DCollection([[(-1.5, -3.2, 0), (11.8, -3.2, 0), (11.8, 3.2, 0), (-1.5, 3.2, 0)]], facecolor='#3a6ea5', alpha=0.18, edgecolor='none')
    ax.add_collection3d(water)
    ax.set_xlim(-1.5, 11.8); ax.set_ylim(-3.2, 3.2); ax.set_zlim(-2.3, 14.4)
    ax.set_box_aspect((13.3, 6.4, 16.7))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    fig.savefig(os.path.join(OUT, 'preview_%s.png' % name), bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('rendu:', name)
print('TERMINE')
