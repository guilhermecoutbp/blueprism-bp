// Vellaro Design, versão 2: do espaço ao móvel.
// Planta baixa, desenho técnico, vista explodida, montagem, uso, ambiente
// completo e configurador de acabamentos, tudo guiado pela rolagem.

import * as THREE from "./vendor/three/three.module.min.js";
import { RoomEnvironment } from "./vendor/three/RoomEnvironment.js";
import { RoundedBoxGeometry } from "./vendor/three/RoundedBoxGeometry.js";
import { LineSegments2 } from "./vendor/three/LineSegments2.js";
import { LineSegmentsGeometry } from "./vendor/three/LineSegmentsGeometry.js";
import { LineMaterial } from "./vendor/three/LineMaterial.js";
import Lenis from "./vendor/lenis/lenis.mjs";
import { createNarrator } from "./narracao.js";

const root = document.documentElement;
const canvas = document.querySelector(".stage");
const texts = [...document.querySelectorAll(".chapter__text")];
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const SILVER = "#c9c6c1";
const WHATSAPP = "5521988094936";

// Armário (metros)
const W = 1.8;
const H = 2.2;
const D = 0.5;
const T = 0.02;
const PLINTH = 0.08;
const NICHE = 0.3;
const SHELVES = [0.95, 1.4, 1.85];
const DRAWER_TOP = 0.6;

// Ambiente (metros)
const RW = 4.2;
const RD = 3.4;
const WALL = 0.15;

const WOODS = {
  nogueira: { name: "nogueira", slat: ["#5a4434", "#46352a"], body: "#3b2f27" },
  freijo: { name: "freijó", slat: ["#86643f", "#6e5133"], body: "#5a4430" },
  carvalho: { name: "carvalho", slat: ["#bf9c72", "#a8865e"], body: "#9a7b58" },
};
const STONES = {
  nero: { name: "mármore preto", base: "#1c1a18", vein: "226,220,210" },
  carrara: { name: "mármore branco", base: "#e6e2dc", vein: "120,116,110" },
};
const METALS = {
  latao: { name: "latão", color: "#bf975c", roughness: 0.3, metalness: 1 },
  preto: { name: "preto fosco", color: "#1b1a19", roughness: 0.55, metalness: 0.5 },
};

const clamp01 = (v) => Math.min(1, Math.max(0, v));
const smooth = (t) => t * t * (3 - 2 * t);
const lerp = (a, b, t) => a + (b - a) * t;
const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);

/* ---------- rolagem suave ---------- */

let lenis = null;
if (!reduced) lenis = new Lenis({ lerp: 0.085, smoothWheel: true });

document.querySelectorAll('a[href^="#"]').forEach((a) => {
  a.addEventListener("click", (e) => {
    const target = document.querySelector(a.getAttribute("href"));
    if (!target) return;
    e.preventDefault();
    if (lenis) lenis.scrollTo(target, { duration: 2.4 });
    else target.scrollIntoView();
  });
});

const scrollY = () => (lenis ? lenis.scroll : window.scrollY);

/* ---------- texturas ---------- */

function canvasTexture(width, height, draw, srgb = true) {
  const c = document.createElement("canvas");
  c.width = width;
  c.height = height;
  draw(c.getContext("2d"), width, height);
  const tex = new THREE.CanvasTexture(c);
  if (srgb) tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

function grain(g, w, h, count, light, dark, maxAlpha) {
  for (let i = 0; i < count; i++) {
    g.strokeStyle = `rgba(${Math.random() < 0.5 ? dark : light},${Math.random() * maxAlpha})`;
    g.lineWidth = 1 + Math.random() * 2;
    const x = Math.random() * w;
    g.beginPath();
    g.moveTo(x, 0);
    g.bezierCurveTo(x + 5, h * 0.3, x - 5, h * 0.7, x + 2, h);
    g.stroke();
  }
}

const slatCache = new Map();
function slatTexture(count, wood) {
  const key = `${count}-${wood.name}`;
  if (slatCache.has(key)) return slatCache.get(key);
  const tex = canvasTexture(512, 1024, (g, w, h) => {
    const grad = g.createLinearGradient(0, 0, w, h);
    grad.addColorStop(0, wood.slat[0]);
    grad.addColorStop(1, wood.slat[1]);
    g.fillStyle = grad;
    g.fillRect(0, 0, w, h);
    grain(g, w, h, 380, "255,235,210", "30,20,12", 0.12);
    const s = w / count;
    for (let i = 0; i <= count; i++) {
      const x = i * s;
      g.fillStyle = "rgba(18,12,8,0.78)";
      g.fillRect(x - 2.5, 0, 5, h);
      g.fillStyle = "rgba(255,235,210,0.12)";
      g.fillRect(x + 2.5, 0, 2, h);
    }
  });
  slatCache.set(key, tex);
  return tex;
}

const marbleCache = new Map();
function marbleTexture(w, h, veins, stone) {
  const key = `${w}x${h}-${stone.base}`;
  if (marbleCache.has(key)) return marbleCache.get(key);
  const tex = canvasTexture(w, h, (g) => {
    g.fillStyle = stone.base;
    g.fillRect(0, 0, w, h);
    g.shadowColor = `rgba(${stone.vein},0.6)`;
    for (let i = 0; i < veins; i++) {
      g.shadowBlur = 4 + Math.random() * 8;
      g.strokeStyle = `rgba(${stone.vein},${0.12 + Math.random() * 0.3})`;
      g.lineWidth = 0.6 + Math.random() * 1.8;
      let x = Math.random() * w;
      let y = -10;
      g.beginPath();
      g.moveTo(x, y);
      while (y < h + 10) {
        x += (Math.random() - 0.35) * 70;
        y += 24 + Math.random() * 36;
        g.lineTo(x, y);
      }
      g.stroke();
    }
  });
  marbleCache.set(key, tex);
  return tex;
}

function glowTexture(cx, cy, rx, ry, rgb = "255,196,128") {
  return canvasTexture(256, 256, (g, w, h) => {
    g.save();
    g.translate(w * cx, h * cy);
    g.scale(rx, ry);
    const r = g.createRadialGradient(0, 0, 0, 0, 0, w / 2);
    r.addColorStop(0, `rgba(${rgb},0.95)`);
    r.addColorStop(0.4, `rgba(${rgb},0.35)`);
    r.addColorStop(1, `rgba(${rgb},0)`);
    g.fillStyle = r;
    g.fillRect(-w, -h, w * 2, h * 2);
    g.restore();
  });
}

// Alfa que some nas bordas, para o ambiente se dissolver no fundo do site
function fadeAlpha(cx, cy, rx, ry) {
  return canvasTexture(
    256,
    256,
    (g, w, h) => {
      g.fillStyle = "#000";
      g.fillRect(0, 0, w, h);
      g.save();
      g.translate(w * cx, h * cy);
      g.scale(rx, ry);
      const r = g.createRadialGradient(0, 0, 0, 0, 0, w / 2);
      r.addColorStop(0, "#fff");
      r.addColorStop(0.3, "#fff");
      r.addColorStop(0.75, "#5a5a5a");
      r.addColorStop(1, "#000");
      g.fillStyle = r;
      g.fillRect(-w * 2, -h * 2, w * 4, h * 4);
      g.restore();
    },
    false,
  );
}

function floorTexture() {
  const tex = canvasTexture(1024, 1024, (g, w, h) => {
    g.fillStyle = "#2a231e";
    g.fillRect(0, 0, w, h);
    const plank = w / 6;
    for (let i = 0; i < 6; i++) {
      const tone = 26 + Math.random() * 14;
      g.fillStyle = `rgb(${tone + 16},${tone + 9},${tone + 3})`;
      g.fillRect(i * plank + 1, 0, plank - 2, h);
      g.save();
      g.beginPath();
      g.rect(i * plank, 0, plank, h);
      g.clip();
      grain(g, w, h, 140, "200,170,140", "10,6,4", 0.08);
      g.restore();
      g.fillStyle = "rgba(0,0,0,0.55)";
      g.fillRect(i * plank, 0, 2, h);
      const cut = Math.random() * h;
      g.fillRect(i * plank, cut, plank, 2);
    }
  });
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(4, 3);
  return tex;
}

function plasterTexture() {
  return canvasTexture(512, 512, (g, w, h) => {
    g.fillStyle = "#1f1d1b";
    g.fillRect(0, 0, w, h);
    for (let i = 0; i < 5000; i++) {
      g.fillStyle = `rgba(${Math.random() < 0.5 ? "255,250,240" : "0,0,0"},${Math.random() * 0.04})`;
      g.fillRect(Math.random() * w, Math.random() * h, 2 + Math.random() * 3, 2 + Math.random() * 3);
    }
  });
}

function rugTexture() {
  return canvasTexture(512, 384, (g, w, h) => {
    g.fillStyle = "#3a332d";
    g.fillRect(0, 0, w, h);
    for (let i = 0; i < 9000; i++) {
      g.fillStyle = `rgba(${Math.random() < 0.5 ? "230,215,195" : "10,8,6"},${Math.random() * 0.07})`;
      g.fillRect(Math.random() * w, Math.random() * h, 1, 2);
    }
    g.strokeStyle = "rgba(200,180,150,0.22)";
    g.lineWidth = 3;
    g.strokeRect(22, 22, w - 44, h - 44);
  });
}

function label(text, height) {
  const px = 72;
  const c = document.createElement("canvas");
  const g = c.getContext("2d");
  g.font = `300 ${px}px Jost, sans-serif`;
  c.width = Math.ceil(g.measureText(text).width) + 16;
  c.height = px + 24;
  g.font = `300 ${px}px Jost, sans-serif`;
  g.fillStyle = SILVER;
  g.textBaseline = "middle";
  g.fillText(text, 8, c.height / 2 + 4);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  const mat = new THREE.MeshBasicMaterial({
    map: tex,
    transparent: true,
    depthWrite: false,
    toneMapped: false,
    opacity: 0,
  });
  return new THREE.Mesh(new THREE.PlaneGeometry((height * c.width) / c.height, height), mat);
}

/* ---------- linhas ---------- */

const lineMaterials = [];
function fatLines(points, width, opacity = 1) {
  const geo = new LineSegmentsGeometry();
  geo.setPositions(points);
  const mat = new LineMaterial({ color: SILVER, linewidth: width, transparent: true, opacity, depthWrite: false });
  mat.toneMapped = false;
  lineMaterials.push(mat);
  const lines = new LineSegments2(geo, mat);
  lines.userData.total = geo.instanceCount;
  lines.userData.opacity = opacity;
  return lines;
}

function reveal(lines, t) {
  lines.geometry.instanceCount = Math.floor(lines.userData.total * clamp01(t));
  lines.visible = t > 0;
}

// Revela uma lista de linhas em sequência, como um traço contínuo
function revealSeq(list, t) {
  const total = list.reduce((n, l) => n + l.userData.total, 0);
  let left = total * clamp01(t);
  list.forEach((l) => {
    const n = Math.min(l.userData.total, Math.max(0, left));
    l.geometry.instanceCount = Math.floor(n);
    l.visible = n > 0;
    left -= l.userData.total;
  });
}

function setOpacity(list, k) {
  list.forEach((l) => (l.material.opacity = l.userData.opacity * k));
}

function rng(seed) {
  let s = seed % 2147483647 || 1;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

// Traço à mão: leve tremor e linhas que passam um pouco das pontas
function sketchify(pts, normal, { amp = 0.004, over = 0.035, step = 0.06, seed = 7 } = {}) {
  const r = rng(seed);
  const out = [];
  const a = V();
  const b = V();
  const dir = V();
  const perp = V();
  for (let i = 0; i < pts.length; i += 6) {
    a.set(pts[i], pts[i + 1], pts[i + 2]);
    b.set(pts[i + 3], pts[i + 4], pts[i + 5]);
    dir.subVectors(b, a);
    const len = dir.length();
    if (len < 1e-5) continue;
    dir.divideScalar(len);
    perp.crossVectors(dir, normal);
    if (perp.lengthSq() < 1e-6) perp.set(0, 1, 0);
    perp.normalize();
    const o0 = r() * over;
    const o1 = r() * over;
    const total = len + o0 + o1;
    const n = Math.max(1, Math.ceil(total / step));
    const phase = r() * Math.PI * 2;
    const freq = 0.8 + r() * 1.6;
    let px = 0;
    let py = 0;
    let pz = 0;
    for (let k = 0; k <= n; k++) {
      const d = -o0 + (total * k) / n;
      const wob = amp * Math.sin(phase + (d / Math.max(len, 0.2)) * Math.PI * freq);
      const x = a.x + dir.x * d + perp.x * wob;
      const y = a.y + dir.y * d + perp.y * wob;
      const z = a.z + dir.z * d + perp.z * wob;
      if (k > 0) out.push(px, py, pz, x, y, z);
      px = x;
      py = y;
      pz = z;
    }
  }
  return out;
}

const BOX_EDGES = [
  [0, 0, 0, 1, 0, 0], [1, 0, 0, 1, 1, 0], [1, 1, 0, 0, 1, 0], [0, 1, 0, 0, 0, 0],
  [0, 0, 1, 1, 0, 1], [1, 0, 1, 1, 1, 1], [1, 1, 1, 0, 1, 1], [0, 1, 1, 0, 0, 1],
  [0, 0, 0, 0, 0, 1], [1, 0, 0, 1, 0, 1], [1, 1, 0, 1, 1, 1], [0, 1, 0, 0, 1, 1],
];

function edgesLocal(sx, sy, sz) {
  const X = [-sx / 2, sx / 2];
  const Y = [-sy / 2, sy / 2];
  const Z = [-sz / 2, sz / 2];
  const out = [];
  for (const [a, b, c, d, e, f] of BOX_EDGES) out.push(X[a], Y[b], Z[c], X[d], Y[e], Z[f]);
  return out;
}

/* ---------- fontes e WebGL ---------- */

async function fontsReady() {
  try {
    await Promise.race([document.fonts.load("300 64px Jost"), new Promise((r) => setTimeout(r, 2500))]);
  } catch {
    /* segue com a fonte de reserva */
  }
}

function supportsWebGL() {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

/* ---------- cena ---------- */

function buildScene(renderer, config) {
  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.5;

  const key = new THREE.DirectionalLight("#fff3e2", 2.1);
  key.position.set(-2.4, 4.4, 3.6);
  key.target.position.set(0, 1, 0.6);
  key.castShadow = true;
  key.shadow.mapSize.set(2048, 2048);
  Object.assign(key.shadow.camera, { left: -3, right: 3, top: 3.4, bottom: -1.5, near: 0.5, far: 12 });
  key.shadow.bias = -0.0004;
  key.shadow.normalBias = 0.02;
  scene.add(key, key.target);
  const rim = new THREE.DirectionalLight("#dfe6ee", 1.0);
  rim.position.set(3, 2.5, -2.5);
  scene.add(rim);
  scene.add(new THREE.HemisphereLight("#ffffff", "#2a241f", 0.5));

  /* materiais configuráveis */
  const fade = [];
  const solid = (p) => {
    const m = new THREE.MeshStandardMaterial({ ...p, transparent: true, opacity: 0 });
    fade.push(m);
    return m;
  };
  const mats = {
    body: solid({ roughness: 0.5 }),
    inner: solid({ color: "#2e251f", roughness: 0.7 }),
    gap: solid({ color: "#0f0d0c", roughness: 1 }),
    slats: solid({ roughness: 0.6 }),
    drawerSlats: solid({ roughness: 0.6 }),
    stoneBack: solid({ roughness: 0.2 }),
    stoneShelf: solid({ roughness: 0.2 }),
    metal: solid({}),
  };
  const ledMat = new THREE.MeshBasicMaterial({ color: "#ffd9a0", transparent: true, opacity: 0, toneMapped: false });

  /* peças do armário */
  const piece = new THREE.Group();
  scene.add(piece);
  const parts = [];
  const sideX = W / 2;
  const gap = 0.003;
  const doorW = sideX - NICHE - T - gap * 2;
  const slatCount = Math.round(doorW / 0.04);
  const drawerW = NICHE * 2 - gap * 2;
  const drawerSlats = Math.round(drawerW / 0.04);

  function makePart(box, opt = {}) {
    const [x0, x1, y0, y1, z0, z1] = box;
    const size = V(x1 - x0, y1 - y0, z1 - z0);
    const center = V((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
    const pivot = opt.pivot || center.clone();
    const group = new THREE.Group();
    const content = new THREE.Group();
    group.add(content);
    content.position.copy(center).sub(pivot);
    const parent = opt.parent;
    group.position.copy(pivot);
    if (parent) group.position.sub(parent.pivot);
    (parent ? parent.group : piece).add(group);

    const minDim = Math.min(size.x, size.y, size.z);
    const geo =
      opt.round === false || minDim < 0.012
        ? new THREE.BoxGeometry(size.x, size.y, size.z)
        : new RoundedBoxGeometry(size.x, size.y, size.z, 2, Math.min(0.005, minDim / 2 - 0.001));
    const mesh = new THREE.Mesh(geo, opt.mat);
    mesh.castShadow = opt.shadow !== false;
    mesh.receiveShadow = opt.shadow !== false;
    content.add(mesh);

    const part = { group, content, mesh, pivot, base: group.position.clone(), explode: opt.explode || V(), order: opt.order ?? 0.5 };
    if (opt.lines !== false) {
      const pts = edgesLocal(size.x, size.y, size.z);
      if (opt.slats) {
        for (let i = 1; i < opt.slats; i++) {
          const x = -size.x / 2 + (size.x * i) / opt.slats;
          pts.push(x, -size.y / 2, size.z / 2, x, size.y / 2, size.z / 2);
        }
      }
      part.clean = fatLines(pts, 1.25, 0.95);
      part.sketch = fatLines(sketchify(pts, V(0, 0, 1), { seed: parts.length * 13 + 5 }), 1, 0.3);
      content.add(part.sketch, part.clean);
    }
    parts.push(part);
    return part;
  }

  const body = mats.body;
  const L = makePart([-sideX, -sideX + T, PLINTH, H, 0, D], { mat: body, explode: V(-0.5, 0, 0.05), order: 0.05 });
  const R = makePart([sideX - T, sideX, PLINTH, H, 0, D], { mat: body, explode: V(0.5, 0, 0.05), order: 0.1 });
  const top = makePart([-sideX + T, sideX - T, H - T, H, 0, D], { mat: body, explode: V(0, 0.42, 0.05), order: 0.2 });
  makePart([-sideX + T, sideX - T, PLINTH, PLINTH + T, 0, D], { mat: body, explode: V(0, -0.14, 0.08), order: 0.15 });
  makePart([-NICHE - T, -NICHE, PLINTH + T, H - T, 0, D], { mat: body, explode: V(-0.24, 0, 0.18), order: 0.25 });
  makePart([NICHE, NICHE + T, PLINTH + T, H - T, 0, D], { mat: body, explode: V(0.24, 0, 0.18), order: 0.3 });
  const nicheFloor = makePart([-NICHE, NICHE, DRAWER_TOP, DRAWER_TOP + T, 0, D], { mat: mats.stoneShelf, explode: V(0, -0.06, 0.32), order: 0.35 });
  const plinth = makePart([-sideX + 0.03, sideX - 0.03, 0, PLINTH, 0.04, D - 0.05], { mat: mats.gap, explode: V(0, -0.3, 0.1), order: 0 });
  const back = makePart([-NICHE, NICHE, DRAWER_TOP + T, H - T, 0, 0.015], {
    mat: [mats.inner, mats.inner, mats.inner, mats.inner, mats.stoneBack, mats.inner],
    explode: V(0, 0, -0.38),
    order: 0.4,
  });
  const shelves = SHELVES.map((y, i) =>
    makePart([-NICHE, NICHE, y, y + 0.025, 0.015, D - 0.02], { mat: mats.stoneShelf, explode: V(0, 0.02, 0.42 + i * 0.1), order: 0.5 + i * 0.05 }),
  );
  const doorL = makePart([-sideX + gap, -NICHE - T - gap, PLINTH + gap, H - gap, D, D + 0.018], {
    mat: [body, body, body, body, mats.slats, body],
    pivot: V(-sideX + gap, (PLINTH + H) / 2, D),
    explode: V(-0.32, 0, 0.9),
    slats: slatCount,
    order: 0.75,
  });
  const doorR = makePart([NICHE + T + gap, sideX - gap, PLINTH + gap, H - gap, D, D + 0.018], {
    mat: [body, body, body, body, mats.slats, body],
    pivot: V(sideX - gap, (PLINTH + H) / 2, D),
    explode: V(0.32, 0, 0.9),
    slats: slatCount,
    order: 0.8,
  });
  const drawer = makePart([-NICHE + gap, NICHE - gap, PLINTH + gap, DRAWER_TOP, D, D + 0.018], {
    mat: [body, body, body, body, mats.drawerSlats, body],
    explode: V(0, -0.04, 0.78),
    slats: drawerSlats,
    order: 0.7,
  });
  // Puxadores acompanham portas e gaveta
  const hx = NICHE + T + 0.044;
  makePart([-hx - 0.006, -hx + 0.006, 0.95, 1.45, D + 0.018, D + 0.034], { mat: mats.metal, parent: doorL, explode: V(0, 0, 0.18), order: 0.9 });
  makePart([hx - 0.006, hx + 0.006, 0.95, 1.45, D + 0.018, D + 0.034], { mat: mats.metal, parent: doorR, explode: V(0, 0, 0.18), order: 0.92 });
  makePart([-0.12, 0.12, DRAWER_TOP - 0.06, DRAWER_TOP - 0.048, D + 0.018, D + 0.034], { mat: mats.metal, parent: drawer, explode: V(0, 0, 0.18), order: 0.88 });

  // Fitas de LED e brilhos
  const glowMats = [];
  const glowPlane = (tex, w, h) => {
    const m = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, opacity: 0, toneMapped: false });
    glowMats.push(m);
    return new THREE.Mesh(new THREE.PlaneGeometry(w, h), m);
  };
  const led = (box, parent) => makePart(box, { mat: ledMat, parent, lines: false, shadow: false, round: false });
  shelves.forEach((s, i) => led([-NICHE + 0.02, NICHE - 0.02, SHELVES[i] - 0.006, SHELVES[i], D - 0.1, D - 0.07], s));
  led([-NICHE + 0.02, NICHE - 0.02, H - T - 0.006, H - T, D - 0.1, D - 0.07], top);
  led([-sideX + 0.06, sideX - 0.06, PLINTH - 0.006, PLINTH, D - 0.08, D - 0.06], plinth);

  const wash = glowTexture(0.5, 0, 1, 0.9);
  const pool = glowTexture(0.5, 0.5, 1, 0.5);
  [...SHELVES, H - T].forEach((y) => {
    const g = glowPlane(wash, NICHE * 2 - 0.02, 0.4);
    g.position.set(0, y - 0.2, 0.017).sub(back.pivot);
    back.group.add(g);
  });
  [nicheFloor, ...shelves.slice(0, 2)].forEach((s) => {
    const g = glowPlane(pool, NICHE * 2, 0.5);
    g.rotation.x = -Math.PI / 2;
    const ty = s === nicheFloor ? DRAWER_TOP + T : SHELVES[shelves.indexOf(s)] + 0.025;
    g.position.set(0, ty + 0.001, D / 2).sub(s.pivot);
    s.group.add(g);
  });

  /* planta baixa */
  const plan = [];
  const seg = (x0, z0, x1, z1) => plan.push(x0, 0, z0, x1, 0, z1);
  const hw = RW / 2;
  // parede do fundo
  seg(-hw - WALL, -WALL, hw + WALL, -WALL);
  seg(-hw, 0, hw, 0);
  // parede da frente
  seg(-hw - WALL, RD + WALL, hw + WALL, RD + WALL);
  seg(-hw, RD, hw, RD);
  // parede esquerda com janela
  const w0 = 1.0;
  const w1 = 2.2;
  seg(-hw - WALL, -WALL, -hw - WALL, w0);
  seg(-hw - WALL, w1, -hw - WALL, RD + WALL);
  seg(-hw, 0, -hw, w0);
  seg(-hw, w1, -hw, RD);
  seg(-hw - WALL, w0, -hw, w0);
  seg(-hw - WALL, w1, -hw, w1);
  seg(-hw - WALL, w0, -hw - WALL, w1);
  seg(-hw - WALL / 2, w0, -hw - WALL / 2, w1);
  seg(-hw, w0, -hw, w1);
  // parede direita com porta
  const d0 = 2.3;
  const d1 = 3.1;
  seg(hw + WALL, -WALL, hw + WALL, d0);
  seg(hw + WALL, d1, hw + WALL, RD + WALL);
  seg(hw, 0, hw, d0);
  seg(hw, d1, hw, RD);
  seg(hw, d0, hw + WALL, d0);
  seg(hw, d1, hw + WALL, d1);
  seg(hw, d1, hw - (d1 - d0), d1);
  const arc = (cx, cz, r, a0, a1, n = 18) => {
    for (let i = 0; i < n; i++) {
      const t0 = a0 + ((a1 - a0) * i) / n;
      const t1 = a0 + ((a1 - a0) * (i + 1)) / n;
      seg(cx + r * Math.cos(t0), cz + r * Math.sin(t0), cx + r * Math.cos(t1), cz + r * Math.sin(t1));
    }
  };
  arc(hw, d1, d1 - d0, Math.PI, Math.PI * 1.5);
  // armário na planta
  seg(-sideX, 0, sideX, 0);
  seg(-sideX, D, sideX, D);
  seg(-sideX, 0, -sideX, D);
  seg(sideX, 0, sideX, D);
  seg(-NICHE, 0, -NICHE, D);
  seg(NICHE, 0, NICHE, D);
  arc(-sideX, D, doorW, 0, Math.PI / 2, 12);
  arc(sideX, D, doorW, Math.PI / 2, Math.PI, 12);
  seg(-sideX, D, -sideX, D + doorW);
  seg(sideX, D, sideX, D + doorW);

  const planGroup = new THREE.Group();
  planGroup.position.y = 0.002;
  scene.add(planGroup);
  const planLines = fatLines(sketchify(plan, V(0, 1, 0), { amp: 0.006, over: 0.06, step: 0.08, seed: 3 }), 1.2, 0.9);
  const planSketch = fatLines(sketchify(plan, V(0, 1, 0), { amp: 0.012, over: 0.1, step: 0.1, seed: 11 }), 1, 0.25);
  planGroup.add(planSketch, planLines);

  const pd = [];
  const tickXZ = (x, z) => pd.push(x - 0.04, 0, z + 0.04, x + 0.04, 0, z - 0.04);
  const fz = RD + WALL + 0.35;
  pd.push(-hw, 0, fz, hw, 0, fz, -hw, 0, RD + WALL + 0.08, -hw, 0, fz + 0.08, hw, 0, RD + WALL + 0.08, hw, 0, fz + 0.08);
  tickXZ(-hw, fz);
  tickXZ(hw, fz);
  const rx = hw + WALL + 0.35;
  pd.push(rx, 0, 0, rx, 0, RD, hw + WALL + 0.08, 0, 0, rx + 0.08, 0, 0, hw + WALL + 0.08, 0, RD, rx + 0.08, 0, RD);
  tickXZ(rx, 0);
  tickXZ(rx, RD);
  const planDims = fatLines(pd, 1, 0.8);
  planGroup.add(planDims);
  const planLabels = [];
  const flatLabel = (text, x, z, h, rotZ = 0) => {
    const l = label(text, h);
    l.rotation.set(-Math.PI / 2, 0, rotZ);
    l.position.set(x, 0.001, z);
    planGroup.add(l);
    planLabels.push(l);
  };
  flatLabel("4200", 0, fz - 0.12, 0.13);
  flatLabel("3400", rx + 0.12, RD / 2, 0.13, Math.PI / 2);
  flatLabel("Armário sob medida", 0, D + 0.75, 0.11);

  /* cotas do desenho na parede */
  const elev = new THREE.Group();
  elev.position.z = 0.001;
  scene.add(elev);
  const dp = [];
  const tick = (x, y) => dp.push(x - 0.025, y - 0.025, 0, x + 0.025, y + 0.025, 0);
  const wy = -0.2;
  dp.push(-W / 2, wy, 0, W / 2, wy, 0, -W / 2, -0.05, 0, -W / 2, wy - 0.05, 0, W / 2, -0.05, 0, W / 2, wy - 0.05, 0);
  tick(-W / 2, wy);
  tick(W / 2, wy);
  const ex = W / 2 + 0.24;
  dp.push(ex, 0, 0, ex, H, 0, W / 2 + 0.05, 0, 0, ex + 0.05, 0, 0, W / 2 + 0.05, H, 0, ex + 0.05, H, 0);
  tick(ex, 0);
  tick(ex, H);
  const ny = H + 0.16;
  dp.push(-NICHE, ny, 0, NICHE, ny, 0, -NICHE, H + 0.05, 0, -NICHE, ny + 0.05, 0, NICHE, H + 0.05, 0, NICHE, ny + 0.05, 0);
  tick(-NICHE, ny);
  tick(NICHE, ny);
  const sx = -W / 2 - 0.22;
  dp.push(sx, SHELVES[0], 0, sx, SHELVES[1], 0, -W / 2 - 0.05, SHELVES[0], 0, sx - 0.05, SHELVES[0], 0, -W / 2 - 0.05, SHELVES[1], 0, sx - 0.05, SHELVES[1], 0);
  tick(sx, SHELVES[0]);
  tick(sx, SHELVES[1]);
  const elevDims = fatLines(dp, 1, 0.85);
  elev.add(elevDims);
  const elevLabels = [
    ["1800", 0, wy + 0.075, 0],
    ["2200", ex + 0.075, H / 2, Math.PI / 2],
    ["600", 0, ny + 0.075, 0],
    ["450", sx - 0.075, (SHELVES[0] + SHELVES[1]) / 2, Math.PI / 2],
  ].map(([t, x, y, r]) => {
    const l = label(t, 0.085);
    l.position.set(x, y, 0);
    l.rotation.z = r;
    elev.add(l);
    return l;
  });

  /* ambiente */
  const room = new THREE.Group();
  scene.add(room);
  const roomMats = [];
  const roomMat = (p) => {
    const m = new THREE.MeshStandardMaterial({ depthWrite: false, ...p, transparent: true, opacity: 0 });
    roomMats.push(m);
    return m;
  };
  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(9, 7),
    roomMat({ map: floorTexture(), roughness: 0.75, alphaMap: fadeAlpha(0.5, 0.42, 1, 1.05) }),
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(0, -0.001, 1.6);
  floor.receiveShadow = true;
  room.add(floor);

  const wallGeo = new THREE.PlaneGeometry(9, 4.2);
  wallGeo.translate(0, 2.1, 0);
  const wall = new THREE.Mesh(wallGeo, roomMat({ map: plasterTexture(), roughness: 0.95, alphaMap: fadeAlpha(0.5, 0.78, 1, 1.15) }));
  wall.position.z = -0.003;
  wall.receiveShadow = true;
  room.add(wall);

  const rug = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 1.7), roomMat({ map: rugTexture(), roughness: 1 }));
  rug.rotation.x = -Math.PI / 2;
  rug.position.set(0, 0.004, 1.65);
  rug.receiveShadow = true;
  room.add(rug);

  const halo = glowPlane(glowTexture(0.5, 0.5, 0.78, 0.86), W + 1.4, H + 1.0);
  halo.position.set(0, H / 2 + 0.05, -0.001);
  room.add(halo);
  const floorGlow = glowPlane(glowTexture(0.5, 0.5, 1, 0.42), W + 1.2, 1.6);
  floorGlow.rotation.x = -Math.PI / 2;
  floorGlow.position.set(0, 0.005, D * 0.7);
  room.add(floorGlow);
  const roomGlows = [halo];

  // Objetos de decoração nas prateleiras
  const decor = [];
  const deco = (mesh, x, y, z) => {
    mesh.material = mesh.material.clone();
    mesh.position.set(x, y, z);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData.y = y;
    room.add(mesh);
    decor.push(mesh);
    return mesh;
  };
  const decoMat = (color, roughness = 0.8, metalness = 0) => roomMat({ color, roughness, metalness, depthWrite: true });
  const vase = (pts, mat) => new THREE.Mesh(new THREE.LatheGeometry(pts.map(([r, y]) => new THREE.Vector2(r, y)), 40), mat);
  const ceramic = decoMat("#c9bfb1", 0.85);
  const darkCeramic = decoMat("#2b2826", 0.6);
  const decoBrass = decoMat("#c29b60", 0.3, 1);
  const shelfTop = (i) => SHELVES[i] + 0.025;
  const nicheTop = DRAWER_TOP + T;
  [0.03, 0.026, 0.034, 0.024, 0.03].reduce((x, w, i) => {
    const h = [0.24, 0.26, 0.22, 0.25, 0.23][i];
    const book = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.17), decoMat(["#3b3530", "#5a4f45", "#2a2622", "#6b5d4f", "#45403a"][i]));
    deco(book, x + w / 2, nicheTop + h / 2, 0.24);
    return x + w + 0.004;
  }, 0.06);
  deco(new THREE.Mesh(new THREE.SphereGeometry(0.045, 32, 16), decoBrass), -0.15, nicheTop + 0.045, 0.26);
  deco(vase([[0, 0], [0.05, 0], [0.075, 0.07], [0.066, 0.18], [0.034, 0.27], [0.038, 0.3], [0.03, 0.3]], ceramic), -0.1, shelfTop(0), 0.25);
  deco(vase([[0, 0], [0.04, 0], [0.09, 0.05], [0.095, 0.06], [0.085, 0.06]], darkCeramic), 0.14, shelfTop(0), 0.25);
  [0.035, 0.03, 0.025].reduce((y, h, i) => {
    const book = new THREE.Mesh(new THREE.BoxGeometry(0.2 - i * 0.02, h, 0.15), decoMat(["#4a423b", "#2f2b27", "#6a5c4e"][i]));
    deco(book, 0.12, y + h / 2, 0.25);
    return y + h;
  }, shelfTop(1));
  deco(vase([[0, 0], [0.03, 0], [0.05, 0.06], [0.045, 0.14], [0.022, 0.19], [0.024, 0.2], [0.018, 0.2]], darkCeramic), -0.14, shelfTop(1), 0.25);
  const ring = deco(new THREE.Mesh(new THREE.TorusGeometry(0.075, 0.009, 16, 48), decoBrass), 0, shelfTop(2) + 0.084, 0.25);
  ring.userData.y = shelfTop(2) + 0.084;

  /* configurador */
  function applyConfig(cfg) {
    const wood = WOODS[cfg.wood];
    const stone = STONES[cfg.stone];
    const metal = METALS[cfg.metal];
    mats.body.color.set(wood.body);
    mats.slats.map = slatTexture(slatCount, wood);
    mats.drawerSlats.map = slatTexture(drawerSlats, wood);
    mats.stoneBack.map = marbleTexture(512, 1024, 12, stone);
    mats.stoneShelf.map = marbleTexture(1024, 256, 8, stone);
    mats.metal.color.set(metal.color);
    mats.metal.roughness = metal.roughness;
    mats.metal.metalness = metal.metalness;
    [mats.slats, mats.drawerSlats, mats.stoneBack, mats.stoneShelf].forEach((m) => (m.needsUpdate = true));
  }
  applyConfig(config);

  return {
    scene,
    key,
    piece,
    parts,
    doorL,
    doorR,
    drawer,
    mats,
    fade,
    ledMat,
    glowMats,
    planLines,
    planSketch,
    planDims,
    planLabels,
    elevDims,
    elevLabels,
    room,
    roomMats,
    roomGlows,
    floorGlow,
    wall,
    decor,
    applyConfig,
  };
}

/* ---------- linha do tempo ---------- */

let vh = window.innerHeight;
let maxScroll = 1;
let keys = [0, 1, 2, 3, 4, 5, 6, 7];

function measure() {
  vh = window.innerHeight;
  maxScroll = Math.max(1, document.documentElement.scrollHeight - vh);
  const y = scrollY();
  keys = [0];
  texts.forEach((t) => {
    const r = t.closest(".chapter").getBoundingClientRect();
    keys.push(Math.min(maxScroll, Math.max(0, y + r.top + r.height / 2 - vh / 2)));
  });
}

const span = (s, a, b) => smooth(clamp01((s - a) / (b - a)));
const at = (i, f) => lerp(keys[i], keys[i + 1], f);

/* ---------- narração ---------- */

const soundButton = document.querySelector(".sound");
const listenButton = document.querySelector(".listen");

const narrator = createNarrator({
  files: ["01-entrada", "02-espaco", "03-desenho", "04-pecas", "05-montagem", "06-dia-a-dia", "07-ambiente", "08-seu-jeito"],
  onChange({ enabled, speaking }) {
    soundButton?.setAttribute("aria-pressed", String(enabled));
    soundButton?.setAttribute("aria-label", enabled ? "Desativar narração" : "Ativar narração");
    soundButton?.classList.toggle("is-speaking", enabled && speaking);
  },
});

soundButton?.addEventListener("click", () => {
  listenButton?.classList.add("is-used");
  narrator.toggle();
});
listenButton?.addEventListener("click", () => {
  listenButton.classList.add("is-used");
  narrator.enable();
});

// Um texto por vez: entra, fica, sai por completo e só então o próximo entra.
// A narração acompanha o texto que está visível.
function updateUI(s) {
  const intro = 1 - span(s, 0, vh * 0.55);
  root.style.setProperty("--intro", intro.toFixed(4));
  root.style.setProperty("--bar", span(s, vh * 0.4, vh * 0.85).toFixed(4));
  if (listenButton) listenButton.style.visibility = intro < 0.05 ? "hidden" : "";
  const hold = vh * 0.16;
  const edge = vh * 0.46;
  let speaking = s < vh * 0.3 ? 0 : -1;
  let strongest = 0.55;
  texts.forEach((t, i) => {
    const d = s - keys[i + 1];
    const lastText = i === texts.length - 1;
    let o;
    let y;
    if (d < 0) {
      o = 1 - span(-d, hold, edge);
      y = (1 - o) * 26;
    } else {
      o = lastText ? 1 : 1 - span(d, hold, edge);
      y = (1 - o) * -26;
    }
    t.style.setProperty("--o", o.toFixed(4));
    t.style.setProperty("--y", `${y.toFixed(2)}px`);
    t.style.visibility = o < 0.005 ? "hidden" : "visible";
    if (o > strongest) {
      strongest = o;
      speaking = i + 1;
    }
  });
  narrator.update(speaking);
}

/* ---------- configurador (interface) ---------- */

const config = { wood: "nogueira", stone: "nero", metal: "latao" };
const quoteLink = document.getElementById("orcamento");

function updateQuote() {
  const msg =
    `Olá! Vim pelo site da Vellaro Design. Gostei do armário em ${WOODS[config.wood].name}, ` +
    `com ${STONES[config.stone].name} e detalhes em ${METALS[config.metal].name}. Gostaria de um orçamento.`;
  if (quoteLink) quoteLink.href = `https://wa.me/${WHATSAPP}?text=${encodeURIComponent(msg)}`;
}
updateQuote();

/* ---------- início ---------- */

async function start() {
  measure();
  root.classList.add("is-live");
  updateUI(scrollY());
  let current = scrollY();
  let last = -1;

  let three = null;
  if (canvas && supportsWebGL()) {
    await fontsReady();
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    renderer.setClearColor(0x000000, 0);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    const camera = new THREE.PerspectiveCamera(30, 1, 0.05, 80);
    three = { renderer, camera, ...buildScene(renderer, config), wide: true, fit: () => 1 };
  }

  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      const { opt, value } = chip.dataset;
      config[opt] = value;
      document.querySelectorAll(`.chip[data-opt="${opt}"]`).forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
      updateQuote();
      if (three) {
        three.applyConfig(config);
        last = -1;
      }
    });
  });

  // Enquadramentos da câmera, um para cada capítulo
  const SHOTS = [
    { az: 0, el: 1.5, fw: 5.6, fh: 5.0, t: [0, 0, 1.55] },
    { az: 0, el: 1.45, fw: 5.0, fh: 4.5, t: [0, 0, 1.6] },
    { az: 0, el: 0, fw: 3.0, fh: 3.25, t: [0, 1.1, 0] },
    { az: 0.62, el: 0.24, fw: 3.9, fh: 3.8, t: [0.05, 1.12, 0.45] },
    { az: 0.5, el: 0.12, fw: 2.7, fh: 3.15, t: [0.1, 1.05, 0.25] },
    { az: 0.3, el: 0.07, fw: 3.2, fh: 3.1, t: [0.05, 1.05, 0.5] },
    { az: -0.45, el: 0.2, fw: 5.4, fh: 4.0, t: [0, 1.2, 0.9] },
    { az: -0.3, el: 0.12, fw: 3.7, fh: 3.4, t: [0, 1.1, 0.45] },
  ];

  const distanceFor = (camera, fw, fh) => {
    const v = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
    return Math.max(fh / 2 / v, fw / 2 / (v * camera.aspect));
  };

  function layout() {
    measure();
    if (!three) return;
    const { renderer, camera } = three;
    const w = window.innerWidth;
    const h = window.innerHeight;
    renderer.setSize(w, h, false);
    lineMaterials.forEach((m) => m.resolution.set(w, h));
    camera.aspect = w / h;
    three.wide = w >= 900;
    const rw = three.wide ? 0.6 : 1;
    const rh = three.wide ? 1 : 0.62;
    three.fit = (shot) => distanceFor(camera, shot.fw / rw, shot.fh / rh);
    last = -1;
  }

  const target = V();
  const tA = V();
  const tB = V();
  function place(s) {
    const t = three;

    // planta baixa
    const planDraw = span(s, vh * 0.4, keys[1]);
    const planDims = span(s, at(0, 0.6), keys[1]);
    const planOut = span(s, at(1, 0.35), at(1, 0.8));
    reveal(t.planSketch, span(s, vh * 0.3, at(0, 0.85)));
    reveal(t.planLines, planDraw);
    reveal(t.planDims, planDims);
    t.planSketch.material.opacity = 0.25 * (1 - planOut);
    t.planLines.material.opacity = 0.9 * (1 - planOut);
    t.planDims.material.opacity = 0.8 * (1 - planOut);
    t.planLabels.forEach((l) => (l.material.opacity = planDims * (1 - planOut)));

    // desenho do móvel na parede
    const sketchIn = span(s, at(1, 0.25), at(1, 0.8));
    const drawIn = span(s, at(1, 0.35), keys[2]);
    const sketchOut = span(s, at(2, 0.0), at(2, 0.3));
    const solids = span(s, at(2, 0.45), at(2, 0.95));
    revealSeq(t.parts.filter((p) => p.sketch).map((p) => p.sketch), sketchIn);
    revealSeq(t.parts.filter((p) => p.clean).map((p) => p.clean), drawIn);
    t.parts.forEach((p) => {
      if (!p.clean) return;
      p.sketch.material.opacity = 0.3 * (1 - sketchOut);
      p.clean.material.opacity = 0.95 * (1 - solids * 0.94);
    });
    const elevIn = span(s, at(1, 0.7), keys[2]);
    const elevOut = span(s, at(2, 0.05), at(2, 0.3));
    reveal(t.elevDims, elevIn);
    t.elevDims.material.opacity = 0.85 * (1 - elevOut);
    t.elevLabels.forEach((l) => (l.material.opacity = elevIn * (1 - elevOut)));

    // volume, vista explodida e montagem
    t.piece.scale.z = Math.max(0.0005, span(s, at(2, 0.0), at(2, 0.4)));
    t.parts.forEach((p) => {
      const out = span(s, at(2, 0.3 + p.order * 0.15), at(2, 0.7 + p.order * 0.15));
      const back = span(s, at(3, 0.05 + p.order * 0.45), at(3, 0.3 + p.order * 0.45));
      p.group.position.copy(p.base).addScaledVector(p.explode, out * (1 - back));
    });
    t.fade.forEach((m) => {
      m.opacity = solids;
      m.depthWrite = solids > 0.6;
    });
    const led = span(s, at(3, 0.7), keys[4]);
    t.ledMat.opacity = led;
    t.glowMats.forEach((m) => (m.opacity = led * 0.85));

    // portas e gaveta
    const close = span(s, at(5, 0.0), at(5, 0.35));
    const open = span(s, at(4, 0.1), at(4, 0.6)) * (1 - close);
    const slide = span(s, at(4, 0.2), at(4, 0.7)) * (1 - close);
    t.doorL.group.rotation.y = -1.75 * open;
    t.doorR.group.rotation.y = 1.75 * open;
    t.drawer.group.position.z = t.drawer.base.z + 0.34 * slide;

    // ambiente ao redor
    const roomIn = span(s, at(5, 0.15), at(5, 0.85));
    t.roomMats.forEach((m) => (m.opacity = roomIn));
    t.wall.scale.y = Math.max(0.001, roomIn);
    t.decor.forEach((d, i) => {
      const k = span(s, at(5, 0.4 + i * 0.05), at(5, 0.6 + i * 0.05));
      d.material.opacity = k;
      d.visible = k > 0.01;
      d.position.y = d.userData.y + (1 - k) * 0.06;
    });
    const glowRoom = span(s, at(5, 0.5), keys[6]);
    t.roomGlows.forEach((g) => (g.material.opacity = glowRoom * 0.55));
    t.floorGlow.material.opacity = Math.max(led * roomIn, 0) * 0.85;
    t.room.visible = roomIn > 0.001;

    // câmera
    let i = 0;
    while (i < keys.length - 2 && s >= keys[i + 1]) i++;
    const k = smooth(clamp01((s - keys[i]) / Math.max(1, keys[i + 1] - keys[i])));
    const A = SHOTS[i];
    const B = SHOTS[Math.min(i + 1, SHOTS.length - 1)];
    const az = lerp(A.az, B.az, k);
    const el = lerp(A.el, B.el, k);
    let dist = lerp(t.fit(A), t.fit(B), k);
    target.lerpVectors(tA.fromArray(A.t), tB.fromArray(B.t), k);

    const w = window.innerWidth;
    const h = window.innerHeight;
    const lift = t.wide ? 0 : span(s, at(6, 0.2), keys[7]);
    if (t.wide) t.camera.setViewOffset(w, h, -w * 0.17, 0, w, h);
    else t.camera.setViewOffset(w, h, 0, h * (0.17 + lift * 0.17), w, h);
    t.camera.updateProjectionMatrix();
    dist *= 1 + lift * 0.45;

    t.camera.position.set(
      target.x + dist * Math.sin(az) * Math.cos(el),
      target.y + dist * Math.sin(el),
      target.z + dist * Math.cos(az) * Math.cos(el),
    );
    t.camera.lookAt(target);
  }

  layout();
  window.addEventListener("resize", layout);
  window.addEventListener("load", layout);
  if (document.fonts) document.fonts.ready.then(layout);

  function frame(time) {
    requestAnimationFrame(frame);
    if (lenis) lenis.raf(time);
    const goal = scrollY();
    current = reduced ? goal : current + (goal - current) * 0.2;
    if (Math.abs(goal - current) < 0.1) current = goal;
    if (current === last) return;
    updateUI(current);
    if (three) {
      place(current);
      three.renderer.render(three.scene, three.camera);
    }
    last = current;
  }
  requestAnimationFrame(frame);
}

start();
