import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
obj = open(os.path.join(HERE, 'First30_JK.obj')).read()
mtl = open(os.path.join(HERE, 'First30_JK.mtl')).read()
data = json.dumps({'obj': obj, 'mtl': mtl}).replace('</', '<\\/')

JS = r"""
const data = JSON.parse(document.getElementById('model-data').textContent);

const mtlCol = {};
let curMtl = null;
for (const line of data.mtl.split('\n')) {
  const p = line.trim().split(/\s+/);
  if (p[0] === 'newmtl') curMtl = p[1];
  if (p[0] === 'Kd' && curMtl) mtlCol[curMtl] = [parseFloat(p[1]), parseFloat(p[2]), parseFloat(p[3])];
}

const verts = [];
const tris = [];   // {a,b,c, color}
const lines = [];  // {a,b, color}
let color = [0.8, 0.8, 0.8];
for (const raw of data.obj.split('\n')) {
  const line = raw.trim();
  if (!line || line.startsWith('#')) continue;
  const p = line.split(/\s+/);
  if (p[0] === 'v') verts.push([parseFloat(p[1]), parseFloat(p[2]), parseFloat(p[3])]);
  else if (p[0] === 'usemtl') color = mtlCol[p[1]] || color;
  else if (p[0] === 'f') {
    const idx = p.slice(1).map(t => { let n = parseInt(t.split('/')[0], 10); return n < 0 ? verts.length + n + 1 : n; });
    for (let i = 1; i < idx.length - 1; i++) tris.push({ a: idx[0] - 1, b: idx[i] - 1, c: idx[i + 1] - 1, color: color });
  } else if (p[0] === 'l') {
    const idx = p.slice(1).map(t => parseInt(t.split('/')[0], 10) - 1);
    for (let i = 0; i < idx.length - 1; i++) lines.push({ a: idx[i], b: idx[i + 1], color: color });
  }
}

let mn = [1e9, 1e9, 1e9], mx = [-1e9, -1e9, -1e9];
for (const v of verts) for (let i = 0; i < 3; i++) { mn[i] = Math.min(mn[i], v[i]); mx[i] = Math.max(mx[i], v[i]); }
const center = [(mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2];
const scale = 6.0 / Math.max(mx[0] - mn[0], mx[1] - mn[1], mx[2] - mn[2]);

function norm(v) { const l = Math.hypot(v[0], v[1], v[2]) || 1; return [v[0] / l, v[1] / l, v[2] / l]; }
function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }

const triPos = [], triNrm = [], triCol = [];
for (const t of tris) {
  const A = verts[t.a], B = verts[t.b], C = verts[t.c];
  const n = norm(cross(sub(B, A), sub(C, A)));
  for (const v of [A, B, C]) {
    triPos.push((v[0] - center[0]) * scale, (v[1] - center[1]) * scale, (v[2] - center[2]) * scale);
    triNrm.push(n[0], n[1], n[2]);
    triCol.push(t.color[0], t.color[1], t.color[2]);
  }
}
const linePos = [], lineCol = [];
for (const l of lines) {
  for (const i of [l.a, l.b]) {
    const v = verts[i];
    linePos.push((v[0] - center[0]) * scale, (v[1] - center[1]) * scale, (v[2] - center[2]) * scale);
    lineCol.push(l.color[0], l.color[1], l.color[2]);
  }
}

const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl', { antialias: true });

function shader(type, src) {
  const s = gl.createShader(type);
  gl.shaderSource(s, src);
  gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw gl.getShaderInfoLog(s);
  return s;
}
function program(vs, fs) {
  const p = gl.createProgram();
  gl.attachShader(p, shader(gl.VERTEX_SHADER, vs));
  gl.attachShader(p, shader(gl.FRAGMENT_SHADER, fs));
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw gl.getProgramInfoLog(p);
  return p;
}

const triProg = program(
  'attribute vec3 aPos; attribute vec3 aNrm; attribute vec3 aCol; uniform mat4 uMVP; varying vec3 vN; varying vec3 vC;' +
  'void main(){ vN = aNrm; vC = aCol; gl_Position = uMVP * vec4(aPos, 1.0); }',
  'precision mediump float; varying vec3 vN; varying vec3 vC;' +
  'void main(){ vec3 n = normalize(vN); float d = max(dot(n, normalize(vec3(0.5, 0.9, 0.6))), 0.0);' +
  'gl_FragColor = vec4(vC * (0.35 + 0.65 * d), 1.0); }'
);
const lineProg = program(
  'attribute vec3 aPos; attribute vec3 aCol; uniform mat4 uMVP; varying vec3 vC;' +
  'void main(){ vC = aCol; gl_Position = uMVP * vec4(aPos, 1.0); }',
  'precision mediump float; varying vec3 vC; void main(){ gl_FragColor = vec4(vC, 1.0); }'
);

function buf(data, itemSize) {
  const b = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, b);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(data), gl.STATIC_DRAW);
  return b;
}
const triBufPos = buf(triPos), triBufNrm = buf(triNrm), triBufCol = buf(triCol);
const lineBufPos = buf(linePos), lineBufCol = buf(lineCol);
const triCount = triPos.length / 3, lineCount = linePos.length / 3;

function perspective(fov, aspect, near, far) {
  const f = 1 / Math.tan(fov / 2), nf = 1 / (near - far);
  return [f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (far + near) * nf, -1, 0, 0, 2 * far * near * nf, 0];
}
function lookAt(eye, ctr, up) {
  const z = norm(sub(eye, ctr));
  const x = norm(cross(up, z));
  const y = cross(z, x);
  return [x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0,
    -(x[0] * eye[0] + x[1] * eye[1] + x[2] * eye[2]),
    -(y[0] * eye[0] + y[1] * eye[1] + y[2] * eye[2]),
    -(z[0] * eye[0] + z[1] * eye[1] + z[2] * eye[2]), 1];
}
function mul(a, b) {
  const o = new Array(16);
  for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) {
    o[j * 4 + i] = a[i] * b[j * 4] + a[4 + i] * b[j * 4 + 1] + a[8 + i] * b[j * 4 + 2] + a[12 + i] * b[j * 4 + 3];
  }
  return o;
}

let az = -0.9, el = 0.28, dist = 11, tx = 0, ty = 0;
let dragging = false, panning = false, lastX = 0, lastY = 0, interacted = false;
const pointers = new Map();
let pinchDist = 0;

canvas.addEventListener('pointerdown', e => {
  pointers.set(e.pointerId, [e.clientX, e.clientY]);
  if (pointers.size === 2) {
    const p = [...pointers.values()];
    pinchDist = Math.hypot(p[0][0] - p[1][0], p[0][1] - p[1][1]);
  }
  dragging = true; panning = (e.button === 2); interacted = true;
  lastX = e.clientX; lastY = e.clientY;
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener('pointermove', e => {
  if (!pointers.has(e.pointerId)) return;
  pointers.set(e.pointerId, [e.clientX, e.clientY]);
  if (pointers.size === 2) {
    const p = [...pointers.values()];
    const d = Math.hypot(p[0][0] - p[1][0], p[0][1] - p[1][1]);
    dist *= pinchDist / d; pinchDist = d;
    dist = Math.max(3, Math.min(40, dist));
    return;
  }
  const dx = e.clientX - lastX, dy = e.clientY - lastY;
  lastX = e.clientX; lastY = e.clientY;
  if (panning) { tx -= dx * 0.01 * dist * 0.1; ty += dy * 0.01 * dist * 0.1; }
  else { az -= dx * 0.008; el = Math.max(-1.4, Math.min(1.4, el + dy * 0.008)); }
});
function endPointer(e) { pointers.delete(e.pointerId); if (pointers.size === 0) dragging = false; }
canvas.addEventListener('pointerup', endPointer);
canvas.addEventListener('pointercancel', endPointer);
canvas.addEventListener('wheel', e => { e.preventDefault(); dist *= (1 + e.deltaY * 0.001); dist = Math.max(3, Math.min(40, dist)); interacted = true; }, { passive: false });
canvas.addEventListener('contextmenu', e => e.preventDefault());

function resize() {
  const dpr = window.devicePixelRatio || 1;
  canvas.width = canvas.clientWidth * dpr;
  canvas.height = canvas.clientHeight * dpr;
  gl.viewport(0, 0, canvas.width, canvas.height);
}
window.addEventListener('resize', resize);

function render() {
  resize();
  if (!interacted) az += 0.004;
  gl.clearColor(0.055, 0.086, 0.125, 1);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);
  const aspect = canvas.width / canvas.height;
  const proj = perspective(0.8, aspect, 0.1, 100);
  const eye = [tx + dist * Math.cos(el) * Math.sin(az), ty + dist * Math.sin(el), dist * Math.cos(el) * Math.cos(az)];
  const view = lookAt(eye, [tx, ty, 0], [0, 0, 1]);
  const mvp = mul(proj, view);

  gl.useProgram(triProg);
  gl.uniformMatrix4fv(gl.getUniformLocation(triProg, 'uMVP'), false, new Float32Array(mvp));
  gl.bindBuffer(gl.ARRAY_BUFFER, triBufPos);
  const aPos = gl.getAttribLocation(triProg, 'aPos');
  gl.enableVertexAttribArray(aPos);
  gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 0, 0);
  gl.bindBuffer(gl.ARRAY_BUFFER, triBufNrm);
  const aNrm = gl.getAttribLocation(triProg, 'aNrm');
  gl.enableVertexAttribArray(aNrm);
  gl.vertexAttribPointer(aNrm, 3, gl.FLOAT, false, 0, 0);
  gl.bindBuffer(gl.ARRAY_BUFFER, triBufCol);
  const aCol = gl.getAttribLocation(triProg, 'aCol');
  gl.enableVertexAttribArray(aCol);
  gl.vertexAttribPointer(aCol, 3, gl.FLOAT, false, 0, 0);
  gl.drawArrays(gl.TRIANGLES, 0, triCount);

  gl.useProgram(lineProg);
  gl.uniformMatrix4fv(gl.getUniformLocation(lineProg, 'uMVP'), false, new Float32Array(mvp));
  gl.bindBuffer(gl.ARRAY_BUFFER, lineBufPos);
  const bPos = gl.getAttribLocation(lineProg, 'aPos');
  gl.enableVertexAttribArray(bPos);
  gl.vertexAttribPointer(bPos, 3, gl.FLOAT, false, 0, 0);
  gl.bindBuffer(gl.ARRAY_BUFFER, lineBufCol);
  const bCol = gl.getAttribLocation(lineProg, 'aCol');
  gl.enableVertexAttribArray(bCol);
  gl.vertexAttribPointer(bCol, 3, gl.FLOAT, false, 0, 0);
  gl.drawArrays(gl.LINES, 0, lineCount);

  requestAnimationFrame(render);
}
render();
"""

HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>First 30 JK - visionneuse 3D interactive</title>
<style>
  html, body { margin: 0; height: 100%; overflow: hidden; background: #0e1620; }
  canvas { display: block; width: 100%; height: 100%; touch-action: none; }
  #info { position: fixed; top: 10px; left: 12px; color: #cfe3f5; font: 13px/1.5 sans-serif; z-index: 10; pointer-events: none; }
</style>
</head>
<body>
<div id="info"><b>First 30 JK</b> &mdash; glisser : orbiter &middot; molette / pincement : zoom &middot; clic droit : d&eacute;placer</div>
<canvas id="c"></canvas>
<script id="model-data" type="application/json">__DATA__</script>
<script>
__JS__
</script>
</body>
</html>
"""

out = HTML.replace('__DATA__', data).replace('__JS__', JS)
path = os.path.join(HERE, 'viewer-standalone.html')
open(path, 'w').write(out)
print('ecrit:', path, '%.0f Ko' % (len(out) / 1024))
