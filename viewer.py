import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection

obj = sys.argv[1] if len(sys.argv) > 1 else 'First30_JK.obj'
out = sys.argv[2] if len(sys.argv) > 2 else 'view.png'

verts, groups = [], {}
cur = None
mtl_col = {}
for line in open(obj):
    if line.startswith('o '):
        cur = line.split()[1]; groups[cur] = {'v': [], 'f': [], 'l': []}
    elif line.startswith('v '):
        verts.append(tuple(map(float, line.split()[1:4])))
    elif line.startswith('f ') and cur:
        groups[cur]['f'].append([int(t.split('/')[0]) - 1 for t in line.split()[1:]])
    elif line.startswith('l ') and cur:
        groups[cur]['l'].append([int(t) - 1 for t in line.split()[1:]])

palette = ['#f4f6f8', '#0a1e4a', '#c9c7bd', '#8f9296', '#eef0f2', '#101820', '#3a3d42',
           '#23262b', '#a51212', '#9aa0a6', '#f7f3e8', '#6d747c', '#b9bec4', '#1c1e22']
fig = plt.figure(figsize=(13, 9), dpi=120)
ax = fig.add_subplot(111, projection='3d')
for k, (name, g) in enumerate(groups.items()):
    col = palette[k % len(palette)]
    if g['f']:
        ax.add_collection3d(Poly3DCollection([[verts[i] for i in fc] for fc in g['f']], facecolor=col, edgecolor='none'))
    segs = []
    for ln in g['l']:
        for a, b in zip(ln, ln[1:]):
            segs.append([verts[a], verts[b]])
    if segs:
        ax.add_collection3d(Line3DCollection(segs, colors=col, linewidths=1.0))
ax.set_xlim(-1.5, 11.8); ax.set_ylim(-2.4, 2.4); ax.set_zlim(-2.3, 14.4)
ax.set_box_aspect((13.3, 4.8, 16.7))
ax.view_init(elev=20, azim=-58)
ax.set_axis_off()
fig.savefig(out, bbox_inches='tight', facecolor='white')
print('rendu enregistre:', out)
