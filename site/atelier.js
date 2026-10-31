// Do desenho ao móvel: um aparador é traçado no papel, ganha volume e recebe
// acabamento conforme a página rola.

import * as THREE from "./vendor/three/three.module.min.js";
import { RoomEnvironment } from "./vendor/three/RoomEnvironment.js";

const section = document.querySelector(".atelier");
const canvas = section?.querySelector(".atelier__canvas");
const steps = section ? [...section.querySelectorAll(".atelier__step")] : [];

const STONE = new THREE.Color("#eeece8");
const MARBLE = new THREE.Color("#141312");
const INK = "#34322f";

// Aparador (metros)
const W = 1.8;
const H = 0.8;
const D = 0.45;
const LEG = 0.22;
const TOP = 0.03;
const BODY_W = 1.76;
const DOOR_T = 0.018;

// Papel
const PAPER_W = 3.0;
const PAPER_H = 2.12;
const PAPER_Y = 0.33;

const clamp01 = (v) => Math.min(1, Math.max(0, v));
const seg = (p, a, b) => {
  const t = clamp01((p - a) / (b - a));
  return t * t * (3 - 2 * t);
};
const lerp = (a, b, t) => a + (b - a) * t;

function supportsWebGL() {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

async function fontsReady() {
  try {
    await Promise.race([
      Promise.all([document.fonts.load("400 64px Jost"), document.fonts.load("300 64px Jost")]),
      new Promise((r) => setTimeout(r, 2500)),
    ]);
  } catch {
    /* segue com a fonte de reserva */
  }
}

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

function paperTexture() {
  return canvasTexture(2048, 1448, (g, w, h) => {
    g.fillStyle = "#f9f8f5";
    g.fillRect(0, 0, w, h);

    // fibras do papel
    for (let i = 0; i < 9000; i++) {
      g.fillStyle = `rgba(120,110,95,${Math.random() * 0.035})`;
      g.fillRect(Math.random() * w, Math.random() * h, 1 + Math.random() * 2, 1);
    }

    // quadriculado
    const step = w / 60;
    g.strokeStyle = "rgba(150,160,170,0.16)";
    g.lineWidth = 1;
    for (let x = step; x < w; x += step) {
      g.beginPath();
      g.moveTo(x, 0);
      g.lineTo(x, h);
      g.stroke();
    }
    for (let y = step; y < h; y += step) {
      g.beginPath();
      g.moveTo(0, y);
      g.lineTo(w, y);
      g.stroke();
    }

    // margem
    g.strokeStyle = INK;
    g.lineWidth = 3;
    g.strokeRect(40, 40, w - 80, h - 80);

    // carimbo
    const bw = 660;
    const bh = 200;
    const bx = w - 40 - bw;
    const by = h - 40 - bh;
    g.fillStyle = "#f9f8f5";
    g.fillRect(bx, by, bw, bh);
    g.lineWidth = 2;
    g.strokeRect(bx, by, bw, bh);
    g.beginPath();
    g.moveTo(bx, by + 92);
    g.lineTo(bx + bw, by + 92);
    g.moveTo(bx + bw / 2, by + 92);
    g.lineTo(bx + bw / 2, by + bh);
    g.stroke();

    g.fillStyle = INK;
    g.textBaseline = "middle";
    g.font = "300 44px Jost, sans-serif";
    g.letterSpacing = "12px";
    g.fillText("VELLARO", bx + 28, by + 38);
    g.font = "300 16px Jost, sans-serif";
    g.letterSpacing = "10px";
    g.fillText("DESIGN", bx + 30, by + 72);
    g.letterSpacing = "0px";
    g.font = "400 26px Jost, sans-serif";
    g.fillText("Aparador sob medida", bx + 370, by + 48);
    g.font = "400 22px Jost, sans-serif";
    g.fillText("Escala 1:20", bx + 28, by + 128);
    g.fillText("Medidas em mm", bx + 28, by + 166);
    g.fillText("Folha 01", bx + bw / 2 + 28, by + 128);
    g.fillText("Projeto exclusivo", bx + bw / 2 + 28, by + 166);
  });
}

function shadowTexture() {
  return canvasTexture(256, 256, (g, w, h) => {
    g.filter = "blur(18px)";
    g.fillStyle = "rgba(40,30,20,0.55)";
    g.fillRect(36, 36, w - 72, h - 72);
  });
}

function radialTexture(rgb, alpha) {
  return canvasTexture(256, 256, (g, w, h) => {
    const r = g.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w / 2);
    r.addColorStop(0, `rgba(${rgb},${alpha})`);
    r.addColorStop(0.55, `rgba(${rgb},${alpha * 0.35})`);
    r.addColorStop(1, `rgba(${rgb},0)`);
    g.fillStyle = r;
    g.fillRect(0, 0, w, h);
  });
}

function slatTexture(count) {
  return canvasTexture(512, 512, (g, w, h) => {
    const grad = g.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, "#5f4938");
    grad.addColorStop(1, "#4f3c2e");
    g.fillStyle = grad;
    g.fillRect(0, 0, w, h);
    for (let i = 0; i < 260; i++) {
      g.strokeStyle = `rgba(${Math.random() < 0.5 ? "30,20,12" : "140,110,80"},${Math.random() * 0.12})`;
      g.lineWidth = 1 + Math.random() * 2;
      const x = Math.random() * w;
      g.beginPath();
      g.moveTo(x, 0);
      g.bezierCurveTo(x + 6, h * 0.3, x - 6, h * 0.7, x + 3, h);
      g.stroke();
    }
    const s = w / count;
    for (let i = 0; i <= count; i++) {
      const x = i * s;
      g.fillStyle = "rgba(20,14,9,0.75)";
      g.fillRect(x - 2, 0, 4, h);
      g.fillStyle = "rgba(255,230,200,0.10)";
      g.fillRect(x + 2, 0, 2, h);
    }
  });
}

function marbleTexture() {
  return canvasTexture(1024, 256, (g, w, h) => {
    g.fillStyle = "#1e1c1a";
    g.fillRect(0, 0, w, h);
    g.shadowColor = "rgba(230,224,214,0.6)";
    for (let i = 0; i < 14; i++) {
      g.shadowBlur = 4 + Math.random() * 6;
      g.strokeStyle = `rgba(224,218,208,${0.12 + Math.random() * 0.3})`;
      g.lineWidth = 0.6 + Math.random() * 1.8;
      let x = Math.random() * w;
      let y = -10;
      g.beginPath();
      g.moveTo(x, y);
      while (y < h + 10) {
        x += (Math.random() - 0.3) * 60;
        y += 20 + Math.random() * 30;
        g.lineTo(x, y);
      }
      g.stroke();
    }
  });
}

function label(text, height) {
  const fontPx = 72;
  const c = document.createElement("canvas");
  const g = c.getContext("2d");
  g.font = `400 ${fontPx}px Jost, sans-serif`;
  const tw = Math.ceil(g.measureText(text).width) + 16;
  c.width = tw;
  c.height = fontPx + 24;
  g.font = `400 ${fontPx}px Jost, sans-serif`;
  g.fillStyle = INK;
  g.textBaseline = "middle";
  g.fillText(text, 8, c.height / 2 + 4);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, toneMapped: false });
  return new THREE.Mesh(new THREE.PlaneGeometry((height * c.width) / c.height, height), mat);
}

// Caixas do aparador: [x0, x1, y0, y1, z0, z1]
function furnitureBoxes() {
  const bodyX = BODY_W / 2;
  const doorGap = 0.004;
  const doorW = (BODY_W - 0.02 - doorGap * 2) / 3;
  const doors = [0, 1, 2].map((i) => {
    const x0 = -bodyX + 0.01 + i * (doorW + doorGap);
    return [x0, x0 + doorW, LEG + 0.012, H - TOP - 0.012, D - DOOR_T, D];
  });
  const legX = bodyX - 0.08;
  const legs = [
    [-legX, 0.06],
    [legX, 0.06],
    [-legX, D - 0.08],
    [legX, D - 0.08],
  ].map(([x, z]) => [x - 0.015, x + 0.015, 0, LEG, z - 0.015, z + 0.015]);
  return {
    body: [-bodyX, bodyX, LEG, H - TOP, 0, D - DOOR_T],
    top: [-W / 2, W / 2, H - TOP, H, -0.0, D + 0.02],
    doors,
    legs,
    led: [-bodyX + 0.1, bodyX - 0.1, LEG - 0.006, LEG, D - 0.08, D - 0.05],
    doorW,
  };
}

function boxEdges(b, out) {
  const [x0, x1, y0, y1, z0, z1] = b;
  const geo = new THREE.EdgesGeometry(new THREE.BoxGeometry(x1 - x0, y1 - y0, z1 - z0));
  const p = geo.attributes.position.array;
  const cx = (x0 + x1) / 2;
  const cy = (y0 + y1) / 2;
  const cz = (z0 + z1) / 2;
  for (let i = 0; i < p.length; i += 3) out.push(p[i] + cx, p[i + 1] + cy, p[i + 2] + cz);
}

function boxMesh(b, material) {
  const [x0, x1, y0, y1, z0, z1] = b;
  const m = new THREE.Mesh(new THREE.BoxGeometry(x1 - x0, y1 - y0, z1 - z0), material);
  m.position.set((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
  return m;
}

function lineSegments(points, material) {
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(points, 3));
  return new THREE.LineSegments(geo, material);
}

async function init() {
  if (!section || !canvas) return;

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!supportsWebGL()) return;

  await fontsReady();

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;

  const scene = new THREE.Scene();
  const bg = STONE.clone();
  scene.background = bg;
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.55;

  const camera = new THREE.PerspectiveCamera(30, 1, 0.05, 50);

  const key = new THREE.DirectionalLight("#fff6ea", 1.8);
  key.position.set(-2.5, 3.5, 3);
  scene.add(key);
  scene.add(new THREE.HemisphereLight("#ffffff", "#3a332c", 0.6));

  // Papel
  const paperMat = new THREE.MeshBasicMaterial({ map: paperTexture(), transparent: true, toneMapped: false });
  const paper = new THREE.Mesh(new THREE.PlaneGeometry(PAPER_W, PAPER_H), paperMat);
  paper.position.set(0, PAPER_Y, -0.004);
  scene.add(paper);

  const paperShadowMat = new THREE.MeshBasicMaterial({
    map: shadowTexture(),
    transparent: true,
    depthWrite: false,
    opacity: 0.55,
    toneMapped: false,
  });
  const paperShadow = new THREE.Mesh(new THREE.PlaneGeometry(PAPER_W * 1.12, PAPER_H * 1.14), paperShadowMat);
  paperShadow.position.set(0.04, PAPER_Y - 0.05, -0.03);
  scene.add(paperShadow);

  // Móvel
  const boxes = furnitureBoxes();
  const piece = new THREE.Group();
  scene.add(piece);

  const linePts = [];
  boxEdges(boxes.body, linePts);
  boxEdges(boxes.top, linePts);
  boxes.doors.forEach((b) => boxEdges(b, linePts));
  const slatCount = Math.round(boxes.doorW / 0.04);
  boxes.doors.forEach(([x0, x1, y0, y1, , z1]) => {
    for (let i = 1; i < slatCount; i++) {
      const x = x0 + ((x1 - x0) * i) / slatCount;
      linePts.push(x, y0, z1, x, y1, z1);
    }
  });
  boxes.legs.forEach((b) => boxEdges(b, linePts));
  boxEdges(boxes.led, linePts);

  const lineMat = new THREE.LineBasicMaterial({ color: INK, transparent: true, toneMapped: false });
  const lines = lineSegments(linePts, lineMat);
  const lineCount = linePts.length / 3;
  piece.add(lines);

  const solids = new THREE.Group();
  piece.add(solids);
  const fadeMats = [];
  const solid = (params) => {
    const m = new THREE.MeshStandardMaterial({ ...params, transparent: true, opacity: 0 });
    fadeMats.push(m);
    return m;
  };
  const lacquer = solid({ color: "#2b2724", roughness: 0.5, metalness: 0 });
  const slats = solid({ map: slatTexture(slatCount), roughness: 0.6 });
  const stone = solid({ map: marbleTexture(), roughness: 0.22 });
  const brass = solid({ color: "#b8925a", roughness: 0.32, metalness: 1 });

  solids.add(boxMesh(boxes.body, lacquer));
  solids.add(boxMesh(boxes.top, [stone, stone, stone, stone, stone, stone]));
  boxes.doors.forEach((b) => solids.add(boxMesh(b, [lacquer, lacquer, lacquer, lacquer, slats, lacquer])));
  boxes.legs.forEach((b) => solids.add(boxMesh(b, brass)));
  const ledMat = new THREE.MeshBasicMaterial({ color: "#ffd9a0", transparent: true, opacity: 0, toneMapped: false });
  solids.add(boxMesh(boxes.led, ledMat));

  // Cotas
  const dims = new THREE.Group();
  dims.position.z = 0.001;
  scene.add(dims);
  const dimMat = new THREE.LineBasicMaterial({ color: INK, transparent: true, opacity: 0, toneMapped: false });
  const tick = (x, y, pts) => pts.push(x - 0.018, y - 0.018, 0, x + 0.018, y + 0.018, 0);
  const dimPts = [];
  // chão
  dimPts.push(-1.2, 0, 0, 1.2, 0, 0);
  // largura
  const wy = -0.13;
  dimPts.push(-W / 2, wy, 0, W / 2, wy, 0);
  dimPts.push(-W / 2, -0.03, 0, -W / 2, wy - 0.04, 0, W / 2, -0.03, 0, W / 2, wy - 0.04, 0);
  tick(-W / 2, wy, dimPts);
  tick(W / 2, wy, dimPts);
  // altura
  const hx = 1.08;
  dimPts.push(hx, 0, 0, hx, H, 0);
  dimPts.push(W / 2 + 0.04, H, 0, hx + 0.04, H, 0);
  tick(hx, 0, dimPts);
  tick(hx, H, dimPts);
  // pés
  const lx = -1.06;
  dimPts.push(lx, 0, 0, lx, LEG, 0);
  dimPts.push(-BODY_W / 2 - 0.04, LEG, 0, lx - 0.04, LEG, 0);
  tick(lx, 0, dimPts);
  tick(lx, LEG, dimPts);
  dims.add(lineSegments(dimPts, dimMat));

  const labels = [];
  const addLabel = (text, x, y, rot = 0) => {
    const l = label(text, 0.065);
    l.position.set(x, y, 0);
    l.rotation.z = rot;
    l.material.opacity = 0;
    dims.add(l);
    labels.push(l);
  };
  addLabel("1800", 0, wy + 0.05);
  addLabel("800", hx + 0.05, H / 2, Math.PI / 2);
  addLabel("220", lx - 0.05, LEG / 2, Math.PI / 2);

  // Profundidade, desenhada no chão quando o móvel ganha volume
  const depth = new THREE.Group();
  scene.add(depth);
  const depthMat = new THREE.LineBasicMaterial({ color: INK, transparent: true, opacity: 0, toneMapped: false });
  const dx = W / 2 + 0.16;
  depth.add(
    lineSegments(
      [dx, 0.002, 0, dx, 0.002, D + 0.02, W / 2 + 0.04, 0.002, D + 0.02, dx + 0.04, 0.002, D + 0.02,
        dx - 0.018, 0.002, -0.018, dx + 0.018, 0.002, 0.018, dx - 0.018, 0.002, D + 0.002, dx + 0.018, 0.002, D + 0.038],
      depthMat,
    ),
  );
  const depthLabel = label("450", 0.065);
  depthLabel.rotation.set(-Math.PI / 2, 0, Math.PI / 2);
  depthLabel.position.set(dx + 0.06, 0.003, D / 2);
  depthLabel.material.opacity = 0;
  depth.add(depthLabel);

  // Sombra e luz do LED no chão
  const contactMat = new THREE.MeshBasicMaterial({
    map: radialTexture("0,0,0", 0.7),
    transparent: true,
    depthWrite: false,
    opacity: 0,
  });
  const contact = new THREE.Mesh(new THREE.PlaneGeometry(2.3, 0.9), contactMat);
  contact.rotation.x = -Math.PI / 2;
  contact.position.set(0, 0.0005, D / 2);
  scene.add(contact);

  const glowMat = new THREE.MeshBasicMaterial({
    map: radialTexture("255,196,128", 0.9),
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    opacity: 0,
    toneMapped: false,
  });
  const glow = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 1.1), glowMat);
  glow.rotation.x = -Math.PI / 2;
  glow.position.set(0, 0.002, D - 0.1);
  scene.add(glow);

  // Câmera
  let width = 1;
  let height = 1;
  let fitFlat = 5;
  let fitBuilt = 4;

  const distanceFor = (fw, fh) => {
    const v = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
    return Math.max(fh / 2 / v, fw / 2 / (v * camera.aspect));
  };

  function layout() {
    const r = section.querySelector(".atelier__stage").getBoundingClientRect();
    width = Math.max(1, Math.round(r.width));
    height = Math.max(1, Math.round(r.height));
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    const wide = width >= 900;
    const portrait = width / height < 0.85;
    // Desloca a cena para dar espaço ao texto: à direita no desktop, para cima no celular
    if (wide) camera.setViewOffset(width, height, -width * 0.14, 0, width, height);
    else if (portrait) camera.setViewOffset(width, height, 0, height * 0.12, width, height);
    else camera.clearViewOffset();
    camera.updateProjectionMatrix();
    const room = wide ? 0.68 : 1;
    fitFlat = portrait ? distanceFor(2.55, 1.5) : distanceFor(PAPER_W * 1.08 / room, PAPER_H * 1.12);
    fitBuilt = portrait ? distanceFor(2.3, 1.2) : distanceFor(2.5 / room, 1.45);
    needsRender = true;
  }

  const target = new THREE.Vector3();
  function place(p) {
    const draw = seg(p, 0.02, 0.28);
    const dimsIn = seg(p, 0.16, 0.3);
    const extrude = seg(p, 0.33, 0.58);
    const orbit = seg(p, 0.3, 0.62);
    const finish = seg(p, 0.62, 0.84);
    const dark = seg(p, 0.66, 0.88);
    const led = seg(p, 0.76, 0.94);
    const drift = seg(p, 0.84, 1);

    lines.geometry.setDrawRange(0, Math.floor((lineCount * draw) / 2) * 2);
    lineMat.opacity = 1 - finish * 0.95;
    lineMat.color.set(INK).lerp(new THREE.Color("#e8e2d8"), dark);

    piece.scale.z = Math.max(0.0005, extrude);

    const dimFade = dimsIn * (1 - seg(p, 0.42, 0.56));
    dimMat.opacity = dimFade;
    labels.forEach((l) => (l.material.opacity = dimFade));
    const depthIn = seg(p, 0.5, 0.6) * (1 - finish);
    depthMat.opacity = depthIn;
    depthLabel.material.opacity = depthIn;

    fadeMats.forEach((m) => {
      m.opacity = finish;
      m.depthWrite = finish > 0.5;
    });
    ledMat.opacity = led;

    paperMat.opacity = 1 - finish;
    paperShadowMat.opacity = 0.55 * (1 - finish);
    paper.position.z = -0.004 - finish * 0.5;
    paperShadow.position.z = -0.03 - finish * 0.5;

    contactMat.opacity = finish * (1 - dark * 0.4);
    glowMat.opacity = led * 0.8;

    bg.copy(STONE).lerp(MARBLE, dark);
    section.classList.toggle("is-dark", dark > 0.5);

    const az = lerp(0, 0.62, orbit) + drift * 0.16;
    const el = lerp(0, 0.3, orbit) + drift * 0.03;
    const dist = lerp(fitFlat, fitBuilt, orbit);
    target.set(0.2 * orbit, lerp(PAPER_Y, 0.38, orbit), lerp(0, D / 2, orbit));
    camera.position.set(
      target.x + dist * Math.sin(az) * Math.cos(el),
      target.y + dist * Math.sin(el),
      target.z + dist * Math.cos(az) * Math.cos(el),
    );
    camera.lookAt(target);

    const active = p < 0.31 ? 0 : p < 0.62 ? 1 : 2;
    steps.forEach((s, i) => s.classList.toggle("is-active", i === active));
    section.classList.toggle("is-start", p < 0.03);
  }

  function scrollProgress() {
    const r = section.getBoundingClientRect();
    const run = r.height - window.innerHeight;
    return run > 0 ? clamp01(-r.top / run) : 1;
  }

  let current = reduced ? 1 : scrollProgress();
  let needsRender = true;
  let visible = true;

  if (reduced) section.classList.add("atelier--static");
  section.classList.add("atelier--ready");
  layout();

  new ResizeObserver(layout).observe(section.querySelector(".atelier__stage"));
  new IntersectionObserver(([e]) => {
    visible = e.isIntersecting;
    if (visible) needsRender = true;
  }).observe(section);

  let last = -1;
  function frame() {
    requestAnimationFrame(frame);
    if (!visible) return;
    if (!reduced) {
      const goal = scrollProgress();
      current += (goal - current) * 0.12;
      if (Math.abs(goal - current) < 0.0005) current = goal;
    }
    if (!needsRender && current === last) return;
    place(current);
    renderer.render(scene, camera);
    last = current;
    needsRender = false;
  }
  frame();
}

init();
