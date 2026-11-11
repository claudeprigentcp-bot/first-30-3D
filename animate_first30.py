import math, os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection

HERE = os.path.dirname(os.path.abspath(__file__))
OBJ = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'First30_JK.obj')
OUT_GIF = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, 'First30_JK_animation.gif')
N = int(sys.argv[3]) if len(sys.argv) > 3 else 48

verts, groups = [], {}
cur = None
for line in open(OBJ):
    if line.startswith('o '):
        cur = line.split()[1]; groups[cur] = {'v': [], 'f': [], 'l': []}
    elif line.startswith('v '):
        verts.append(tuple(map(float, line.split()[1:4])))
    elif line.startswith('f ') and cur:
        groups[cur]['f'].append([int(t.split('/')[0]) - 1 for t in line.split()[1:]])
    elif line.startswith('l ') and cur:
        groups[cur]['l'].append([int(t) - 1 for t in line.split()[1:]])

colors = {'Hull': '#f4f6f8', 'Stripe': '#0a1e4a', 'Deck': '#c9c7bd', 'Benches': '#8f9296', 'Coachroof': '#eef0f2',
          'Windows': '#101820', 'Hatch': '#3a3d42', 'Keel': '#23262b', 'Bulb': '#a51212', 'Rudders': '#23262b',
          'Mast': '#9aa0a6', 'Boom': '#9aa0a6', 'Sprit': '#9aa0a6', 'Mainsail': '#f7f3e8', 'Jib': '#f2ecdc',
          'Rigging': '#6d747c', 'Railings': '#b9bec4', 'Wheels': '#1c1e22'}

FRAMES = '/tmp/first30_frames'
os.makedirs(FRAMES, exist_ok=True)
for f in os.listdir(FRAMES):
    os.remove(os.path.join(FRAMES, f))

az0, el0 = -58, 16
for k in range(N):
    t = k / N
    az = az0 + 360 * t
    el = el0 + 4 * math.sin(2 * math.pi * t)
    roll = math.radians(5.0 * math.sin(2 * math.pi * t))
    cr, sr = math.cos(roll), math.sin(roll)
    rv = [(x, y * cr - z * sr, y * sr + z * cr) for (x, y, z) in verts]
    fig = plt.figure(figsize=(10, 7.2), dpi=95)
    ax = fig.add_subplot(111, projection='3d')
    for name, g in groups.items():
        col = colors.get(name, '#cccccc')
        if g['f']:
            ax.add_collection3d(Poly3DCollection([[rv[i] for i in fc] for fc in g['f']], facecolor=col, edgecolor='none'))
        segs = []
        for ln in g['l']:
            for a, b in zip(ln, ln[1:]):
                segs.append([rv[a], rv[b]])
        if segs:
            ax.add_collection3d(Line3DCollection(segs, colors=col, linewidths=0.9))
    ax.add_collection3d(Poly3DCollection([[(-2.0, -3.6, 0), (12.4, -3.6, 0), (12.4, 3.6, 0), (-2.0, 3.6, 0)]], facecolor='#3a6ea5', alpha=0.18, edgecolor='none'))
    ax.set_xlim(-2.0, 12.4); ax.set_ylim(-3.6, 3.6); ax.set_zlim(-2.6, 14.6)
    ax.set_box_aspect((14.4, 7.2, 17.2))
    ax.view_init(elev=el, azim=az)
    ax.set_axis_off()
    fig.savefig(os.path.join(FRAMES, 'frame_%03d.png' % k), bbox_inches='tight', facecolor='white')
    plt.close(fig)
    if k % 8 == 0:
        print('frame %d/%d' % (k + 1, N))

from PIL import Image
imgs = [Image.open(os.path.join(FRAMES, 'frame_%03d.png' % k)).convert('P', palette=Image.ADAPTIVE, colors=128) for k in range(N)]
imgs[0].save(OUT_GIF, save_all=True, append_images=imgs[1:], duration=70, loop=0, optimize=True)
print('GIF ecrit:', OUT_GIF, '%.1f Mo' % (os.path.getsize(OUT_GIF) / 1e6))
