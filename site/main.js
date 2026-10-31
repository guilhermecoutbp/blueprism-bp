// Vellaro Design: um armário é desenhado, medido, ganha volume e recebe
// acabamento conforme a página rola. Tudo sobre o mesmo fundo escuro.

import * as THREE from "./vendor/three/three.module.min.js";
import { RoomEnvironment } from "./vendor/three/RoomEnvironment.js";
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

// Armário (metros)
const W = 1.8;
const H = 2.2;
const D = 0.5;
const T = 0.02; // espessura das chapas
const PLINTH = 0.08;
const NICHE = 0.3; // metade da largura do nicho central
const SHELVES = [0.95, 1.4, 1.85];
const DRAWER_TOP = 0.6;

const clamp01 = (v) => Math.min(1, Math.max(0, v));
const smooth = (t) => t * t * (3 - 2 * t);
const lerp = (a, b, t) => a + (b - a) * t;

/* ---------- rolagem suave ---------- */

let lenis = null;
if (!reduced) {
  lenis = new Lenis({ lerp: 0.085, smoothWheel: true });
}

document.querySelectorAll('a[href^="#"]').forEach((a) => {
  a.addEventListener("click", (e) => {
    const target = document.querySelector(a.getAttribute("href"));
    if (!target) return;
    e.preventDefault();
    if (lenis) lenis.scrollTo(target, { duration: 2.2 });
    else target.scrollIntoView();
  });
});

const scrollY = () => (lenis ? lenis.scroll : window.scrollY);

/* ---------- texturas ---------- */

function canvasTexture(width, height, draw) {
  const c = document.createElement("canvas");
  c.width = width;
  c.height = height;
  draw(c.getContext("2d"), width, height);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

function slatTexture(count) {
  return canvasTexture(512, 1024, (g, w, h) => {
    const grad = g.createLinearGradient(0, 0, w, h);
    grad.addColorStop(0, "#5a4434");
    grad.addColorStop(1, "#46352a");
    g.fillStyle = grad;
    g.fillRect(0, 0, w, h);
    for (let i = 0; i < 380; i++) {
      g.strokeStyle = `rgba(${Math.random() < 0.5 ? "30,20,12" : "150,118,86"},${Math.random() * 0.12})`;
      g.lineWidth = 1 + Math.random() * 2;
      const x = Math.random() * w;
      g.beginPath();
      g.moveTo(x, 0);
      g.bezierCurveTo(x + 5, h * 0.3, x - 5, h * 0.7, x + 2, h);
      g.stroke();
    }
    const s = w / count;
    for (let i = 0; i <= count; i++) {
      const x = i * s;
      g.fillStyle = "rgba(18,12,8,0.8)";
      g.fillRect(x - 2.5, 0, 5, h);
      g.fillStyle = "rgba(255,230,200,0.1)";
      g.fillRect(x + 2.5, 0, 2, h);
    }
  });
}

function marbleTexture(w, h, veins) {
  return canvasTexture(w, h, (g) => {
    g.fillStyle = "#1c1a18";
    g.fillRect(0, 0, w, h);
    g.shadowColor = "rgba(230,224,214,0.6)";
    for (let i = 0; i < veins; i++) {
      g.shadowBlur = 4 + Math.random() * 8;
      g.strokeStyle = `rgba(226,220,210,${0.12 + Math.random() * 0.3})`;
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
}

function glowTexture(cx, cy, rx, ry) {
  // brilho elíptico quente, centrado em (cx, cy) relativo ao tamanho
  return canvasTexture(256, 256, (g, w, h) => {
    g.save();
    g.translate(w * cx, h * cy);
    g.scale(rx, ry);
    const r = g.createRadialGradient(0, 0, 0, 0, 0, w / 2);
    r.addColorStop(0, "rgba(255,200,140,0.95)");
    r.addColorStop(0.4, "rgba(255,190,120,0.35)");
    r.addColorStop(1, "rgba(255,180,110,0)");
    g.fillStyle = r;
    g.fillRect(-w, -h, w * 2, h * 2);
    g.restore();
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

/* ---------- geometria do armário ---------- */

// Caixa = [x0, x1, y0, y1, z0, z1]
function cabinet() {
  const sideX = W / 2;
  const doorGap = 0.003;
  const parts = {
    carcass: [
      [-sideX, -sideX + T, PLINTH, H, 0, D], // lateral esquerda
      [sideX - T, sideX, PLINTH, H, 0, D], // lateral direita
      [-sideX + T, sideX - T, H - T, H, 0, D], // tampo
      [-sideX + T, sideX - T, PLINTH, PLINTH + T, 0, D], // base
      [-NICHE - T, -NICHE, PLINTH + T, H - T, 0, D], // divisória esquerda
      [NICHE, NICHE + T, PLINTH + T, H - T, 0, D], // divisória direita
      [-NICHE, NICHE, DRAWER_TOP, DRAWER_TOP + T, 0, D], // fundo do nicho
    ],
    plinth: [-sideX + 0.03, sideX - 0.03, 0, PLINTH, 0.04, D - 0.05],
    back: [-NICHE, NICHE, DRAWER_TOP, H - T, 0, 0.015],
    shelves: SHELVES.map((y) => [-NICHE, NICHE, y, y + 0.025, 0.015, D - 0.02]),
    drawer: [-NICHE + doorGap, NICHE - doorGap, PLINTH + doorGap, DRAWER_TOP, D, D + 0.018],
    doors: [
      [-sideX + doorGap, -NICHE - T - doorGap, PLINTH + doorGap, H - doorGap, D, D + 0.018],
      [NICHE + T + doorGap, sideX - doorGap, PLINTH + doorGap, H - doorGap, D, D + 0.018],
    ],
    handles: [
      [-NICHE - T - 0.05, -NICHE - T - 0.038, 0.95, 1.45, D + 0.018, D + 0.034],
      [NICHE + T + 0.038, NICHE + T + 0.05, 0.95, 1.45, D + 0.018, D + 0.034],
      [-0.12, 0.12, DRAWER_TOP - 0.06, DRAWER_TOP - 0.048, D + 0.018, D + 0.034],
    ],
    leds: [
      ...SHELVES.map((y) => [-NICHE + 0.02, NICHE - 0.02, y - 0.006, y, D - 0.1, D - 0.07]),
      [-NICHE + 0.02, NICHE - 0.02, H - T - 0.006, H - T, D - 0.1, D - 0.07],
    ],
    plinthLed: [-sideX + 0.06, sideX - 0.06, PLINTH - 0.006, PLINTH, D - 0.08, D - 0.06],
  };
  parts.doorW = parts.doors[0][1] - parts.doors[0][0];
  return parts;
}

const BOX_EDGES = [
  [0, 0, 0, 1, 0, 0], [1, 0, 0, 1, 1, 0], [1, 1, 0, 0, 1, 0], [0, 1, 0, 0, 0, 0],
  [0, 0, 1, 1, 0, 1], [1, 0, 1, 1, 1, 1], [1, 1, 1, 0, 1, 1], [0, 1, 1, 0, 0, 1],
  [0, 0, 0, 0, 0, 1], [1, 0, 0, 1, 0, 1], [1, 1, 0, 1, 1, 1], [0, 1, 0, 0, 1, 1],
];

function boxEdges([x0, x1, y0, y1, z0, z1], out, jitter = 0) {
  const X = [x0, x1];
  const Y = [y0, y1];
  const Z = [z0, z1];
  const j = () => (Math.random() - 0.5) * jitter;
  for (const [a, b, c, d, e, f] of BOX_EDGES) {
    out.push(X[a] + j(), Y[b] + j(), Z[c], X[d] + j(), Y[e] + j(), Z[f]);
  }
}

function boxMesh([x0, x1, y0, y1, z0, z1], material) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, y1 - y0, z1 - z0), material);
  m.position.set((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
  return m;
}

const lineMaterials = [];
function fatLines(points, width, opacity = 1) {
  const geo = new LineSegmentsGeometry();
  geo.setPositions(points);
  const mat = new LineMaterial({
    color: SILVER,
    linewidth: width,
    transparent: true,
    opacity,
    depthWrite: false,
  });
  mat.toneMapped = false;
  lineMaterials.push(mat);
  const lines = new LineSegments2(geo, mat);
  lines.userData.total = geo.instanceCount;
  return lines;
}

const reveal = (lines, t) => {
  lines.geometry.instanceCount = Math.floor(lines.userData.total * t);
  lines.visible = t > 0;
};

/* ---------- cena ---------- */

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

function buildScene(renderer) {
  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.5;

  const key = new THREE.DirectionalLight("#fff3e2", 2.1);
  key.position.set(-2.5, 3.5, 3.5);
  scene.add(key);
  const rim = new THREE.DirectionalLight("#dfe6ee", 1.1);
  rim.position.set(3, 2.5, -2.5);
  scene.add(rim);
  scene.add(new THREE.HemisphereLight("#ffffff", "#2a241f", 0.5));

  const c = cabinet();
  const piece = new THREE.Group();
  scene.add(piece);

  // Linhas de construção: o esboço que antecede o desenho
  const guide = [];
  const gx = [-W / 2, -NICHE - T, NICHE + T, W / 2];
  const gy = [0, PLINTH, DRAWER_TOP, ...SHELVES, H];
  gx.forEach((x) => guide.push(x, -0.35, 0, x, H + 0.35, 0));
  gy.forEach((y) => guide.push(-W / 2 - 0.5, y, 0, W / 2 + 0.5, y, 0));
  const guides = fatLines(guide, 1, 0.16);
  scene.add(guides);

  // Traço do móvel (limpo) e o rascunho a lápis por baixo
  const all = [...c.carcass, c.plinth, c.back, ...c.shelves, c.drawer, ...c.doors, ...c.handles];
  const clean = [];
  const sketch = [];
  all.forEach((b) => {
    boxEdges(b, clean);
    boxEdges(b, sketch, 0.012);
  });
  const slatCount = Math.round(c.doorW / 0.04);
  c.doors.forEach(([x0, x1, y0, y1, , z1]) => {
    for (let i = 1; i < slatCount; i++) {
      const x = x0 + ((x1 - x0) * i) / slatCount;
      clean.push(x, y0, z1, x, y1, z1);
    }
  });
  const drawerSlats = Math.round((c.drawer[1] - c.drawer[0]) / 0.04);
  for (let i = 1; i < drawerSlats; i++) {
    const [x0, x1, y0, y1, , z1] = c.drawer;
    const x = x0 + ((x1 - x0) * i) / drawerSlats;
    clean.push(x, y0, z1, x, y1, z1);
  }
  const sketchLines = fatLines(sketch, 1, 0.32);
  const cleanLines = fatLines(clean, 1.25, 0.95);
  piece.add(sketchLines, cleanLines);

  // Cotas
  const dims = new THREE.Group();
  scene.add(dims);
  const dp = [];
  const tick = (x, y) => dp.push(x - 0.025, y - 0.025, 0, x + 0.025, y + 0.025, 0);
  const wy = -0.2;
  dp.push(-W / 2, wy, 0, W / 2, wy, 0, -W / 2, -0.05, 0, -W / 2, wy - 0.05, 0, W / 2, -0.05, 0, W / 2, wy - 0.05, 0);
  tick(-W / 2, wy);
  tick(W / 2, wy);
  const hx = W / 2 + 0.24;
  dp.push(hx, 0, 0, hx, H, 0, W / 2 + 0.05, 0, 0, hx + 0.05, 0, 0, W / 2 + 0.05, H, 0, hx + 0.05, H, 0);
  tick(hx, 0);
  tick(hx, H);
  const ny = H + 0.16;
  dp.push(-NICHE, ny, 0, NICHE, ny, 0, -NICHE, H + 0.05, 0, -NICHE, ny + 0.05, 0, NICHE, H + 0.05, 0, NICHE, ny + 0.05, 0);
  tick(-NICHE, ny);
  tick(NICHE, ny);
  const sx = -W / 2 - 0.22;
  dp.push(sx, SHELVES[0], 0, sx, SHELVES[1], 0, -W / 2 - 0.05, SHELVES[0], 0, sx - 0.05, SHELVES[0], 0, -W / 2 - 0.05, SHELVES[1], 0, sx - 0.05, SHELVES[1], 0);
  tick(sx, SHELVES[0]);
  tick(sx, SHELVES[1]);
  const dimLines = fatLines(dp, 1, 0.85);
  dims.add(dimLines);
  const labels = [
    ["1800", 0, wy + 0.075, 0],
    ["2200", hx + 0.075, H / 2, Math.PI / 2],
    ["600", 0, ny + 0.075, 0],
    ["450", sx - 0.075, (SHELVES[0] + SHELVES[1]) / 2, Math.PI / 2],
  ].map(([t, x, y, r]) => {
    const l = label(t, 0.085);
    l.position.set(x, y, 0);
    l.rotation.z = r;
    dims.add(l);
    return l;
  });

  // Profundidade, no chão
  const dx = W / 2 + 0.2;
  const depthPts = [dx, 0, 0, dx, 0, D + 0.018, W / 2 + 0.05, 0, D + 0.018, dx + 0.05, 0, D + 0.018, W / 2 + 0.05, 0, 0, dx + 0.05, 0, 0];
  depthPts.push(dx - 0.025, 0, -0.025, dx + 0.025, 0, 0.025, dx - 0.025, 0, D - 0.007, dx + 0.025, 0, D + 0.043);
  const depthLines = fatLines(depthPts, 1, 0.85);
  scene.add(depthLines);
  const depthLabel = label("500", 0.085);
  depthLabel.rotation.set(-Math.PI / 2, 0, Math.PI / 2);
  depthLabel.position.set(dx + 0.08, 0.002, D / 2);
  scene.add(depthLabel);

  // Materiais
  const fade = [];
  const solid = (p) => {
    const m = new THREE.MeshStandardMaterial({ ...p, transparent: true, opacity: 0 });
    fade.push(m);
    return m;
  };
  const oak = solid({ color: "#3b2f27", roughness: 0.5 });
  const inner = solid({ color: "#3a2f27", roughness: 0.7 });
  const shadowGap = solid({ color: "#0f0d0c", roughness: 1 });
  const slats = solid({ map: slatTexture(slatCount), roughness: 0.6 });
  const drawerSlatsMat = solid({ map: slatTexture(drawerSlats), roughness: 0.6 });
  const marble = solid({ map: marbleTexture(512, 1024, 12), roughness: 0.2 });
  const marbleShelf = solid({ map: marbleTexture(1024, 256, 8), roughness: 0.2 });
  const brass = solid({ color: "#bf975c", roughness: 0.3, metalness: 1 });

  const solids = new THREE.Group();
  piece.add(solids);
  c.carcass.forEach((b) => solids.add(boxMesh(b, oak)));
  solids.add(boxMesh(c.plinth, shadowGap));
  solids.add(boxMesh(c.back, [inner, inner, inner, inner, marble, inner]));
  c.shelves.forEach((b) => solids.add(boxMesh(b, marbleShelf)));
  solids.add(boxMesh(c.drawer, [oak, oak, oak, oak, drawerSlatsMat, oak]));
  c.doors.forEach((b) => solids.add(boxMesh(b, [oak, oak, oak, oak, slats, oak])));
  c.handles.forEach((b) => solids.add(boxMesh(b, brass)));

  // Luz: fitas de LED, brilho nas prateleiras e no chão
  const ledMat = new THREE.MeshBasicMaterial({ color: "#ffd9a0", transparent: true, opacity: 0, toneMapped: false });
  [...c.leds, c.plinthLed].forEach((b) => solids.add(boxMesh(b, ledMat)));

  const glowMats = [];
  const glowPlane = (tex, w, h) => {
    const m = new THREE.MeshBasicMaterial({
      map: tex,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      opacity: 0,
      toneMapped: false,
    });
    glowMats.push(m);
    return new THREE.Mesh(new THREE.PlaneGeometry(w, h), m);
  };
  const wash = glowTexture(0.5, 0, 1, 0.9);
  [...SHELVES, H - T].forEach((y) => {
    const g = glowPlane(wash, NICHE * 2 - 0.02, 0.4);
    g.position.set(0, y - 0.2, 0.017);
    solids.add(g);
    const s = glowPlane(glowTexture(0.5, 0.5, 1, 0.5), NICHE * 2, 0.5);
    s.rotation.x = -Math.PI / 2;
    const below = [DRAWER_TOP + T, ...SHELVES.map((v) => v + 0.025)].filter((v) => v < y).pop();
    s.position.set(0, below + 0.001, D / 2);
    solids.add(s);
  });
  const floorGlow = glowPlane(glowTexture(0.5, 0.5, 1, 0.42), W + 1.2, 1.6);
  floorGlow.rotation.x = -Math.PI / 2;
  floorGlow.position.set(0, 0.001, D * 0.7);
  scene.add(floorGlow);

  return {
    scene,
    piece,
    guides,
    sketchLines,
    cleanLines,
    dimLines,
    labels,
    depthLines,
    depthLabel,
    fade,
    ledMat,
    glowMats,
  };
}

/* ---------- linha do tempo ---------- */

let vh = window.innerHeight;
let maxScroll = 1;
let keys = [0, 1, 2, 3, 4, 5];

// Cada capítulo tem um ponto da rolagem em que fica centralizado na tela.
// O móvel e os textos usam esses pontos como marcos.
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
    const camera = new THREE.PerspectiveCamera(30, 1, 0.05, 60);
    three = { renderer, camera, ...buildScene(renderer), fitFlat: 8, fitBuilt: 6 };
  }

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
    const wide = w >= 900;
    // Abre espaço para o texto: móvel à direita no desktop, no alto no celular
    three.wide = wide;
    if (wide) camera.setViewOffset(w, h, -w * 0.17, 0, w, h);
    else camera.setViewOffset(w, h, 0, h * 0.17, w, h);
    camera.updateProjectionMatrix();
    const rw = wide ? 0.6 : 1;
    const rh = wide ? 1 : 0.62;
    three.fitFlat = distanceFor(camera, 3.0 / rw, 3.2 / rh);
    three.fitBuilt = distanceFor(camera, 2.7 / rw, 3.15 / rh);
    last = -1;
  }

  const target = new THREE.Vector3();
  function place(s) {
    const t = three;
    const construct = span(s, vh * 0.3, at(0, 0.8));
    const draw = span(s, vh * 0.45, keys[1]);
    const sketchIn = span(s, vh * 0.35, at(0, 0.9));
    const dims = span(s, at(1, 0.15), keys[2]);
    const dimsOut = span(s, at(2, 0.4), at(2, 0.8));
    const extrude = span(s, at(2, 0.3), keys[3]);
    const orbit = span(s, at(2, 0.15), at(3, 0.1));
    const finish = span(s, at(3, 0.15), keys[4]);
    const led = span(s, at(3, 0.6), at(4, 0.3));
    const drift = span(s, keys[4], keys[5]);

    reveal(t.guides, construct);
    t.guides.material.opacity = 0.16 * (1 - span(s, at(2, 0.2), at(2, 0.7)));
    reveal(t.sketchLines, sketchIn);
    t.sketchLines.material.opacity = 0.32 * (1 - span(s, at(1, 0.2), at(2, 0.3)));
    reveal(t.cleanLines, draw);
    t.cleanLines.material.opacity = 0.95 * (1 - finish * 0.92);

    reveal(t.dimLines, dims);
    t.dimLines.material.opacity = 0.85 * (1 - dimsOut);
    t.labels.forEach((l) => (l.material.opacity = dims * (1 - dimsOut)));
    const depth = span(s, at(2, 0.75), keys[3]) * (1 - span(s, at(3, 0.2), at(3, 0.6)));
    reveal(t.depthLines, depth > 0 ? 1 : 0);
    t.depthLines.material.opacity = 0.85 * depth;
    t.depthLabel.material.opacity = depth;

    t.piece.scale.z = Math.max(0.0005, extrude);

    t.fade.forEach((m) => {
      m.opacity = finish;
      m.depthWrite = finish > 0.6;
    });
    t.ledMat.opacity = led;
    t.glowMats.forEach((m) => (m.opacity = led * 0.85));

    const az = lerp(0, 0.6, orbit) + drift * 0.22;
    const el = lerp(0, 0.16, orbit) + drift * 0.04;
    // No celular o móvel sobe e se afasta no fim para dar lugar ao contato
    const lift = t.wide ? 0 : drift;
    const dist = lerp(t.fitFlat, t.fitBuilt, orbit) * (1 - drift * 0.05 + lift * 0.55);
    if (!t.wide) {
      const w = window.innerWidth;
      const h = window.innerHeight;
      t.camera.setViewOffset(w, h, 0, h * (0.17 + lift * 0.14), w, h);
      t.camera.updateProjectionMatrix();
    }
    target.set(0.15 * orbit, lerp(H / 2 + 0.02, H / 2 - 0.05, orbit), lerp(0, D / 2, orbit));
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
