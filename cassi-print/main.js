// Cassi Print: a impressora da abertura imprime um vaso de gatinho camada por
// camada conforme a página rola. Também cuida dos links de WhatsApp, do
// formulário de pedido e dos avisos que aparecem de tempos em tempos.

import * as THREE from "./vendor/three/three.module.min.js";
import { RoomEnvironment } from "./vendor/three/RoomEnvironment.js";
import Lenis from "./vendor/lenis/lenis.mjs";

const WHATSAPP = "5511964635923";
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const root = document.documentElement;

const waLink = (msg) => `https://wa.me/${WHATSAPP}?text=${encodeURIComponent(msg)}`;

/* ---------- links de WhatsApp com mensagem pronta ---------- */

document.querySelectorAll("[data-wa]").forEach((a) => {
  a.href = waLink(a.dataset.wa);
});

/* ---------- rolagem suave ---------- */

let lenis = null;
if (!reduced) lenis = new Lenis({ lerp: 0.09, smoothWheel: true });

document.querySelectorAll('a[href^="#"]').forEach((a) => {
  a.addEventListener("click", (e) => {
    const target = document.querySelector(a.getAttribute("href"));
    if (!target) return;
    e.preventDefault();
    if (lenis) lenis.scrollTo(target, { offset: -70, duration: 1.6 });
    else target.scrollIntoView();
  });
});

const scrollY = () => (lenis ? lenis.scroll : window.scrollY);

/* ---------- depoimentos ---------- */

// Coloque aqui apenas depoimentos reais de clientes, por exemplo:
// { texto: "Ficou perfeito, igualzinho ao meu gato!", nome: "Ana", cidade: "Campinas, SP" }
// Enquanto a lista estiver vazia, a seção fica escondida.
const DEPOIMENTOS = [];

if (DEPOIMENTOS.length) {
  const box = document.querySelector(".quotes");
  DEPOIMENTOS.forEach((d) => {
    const q = document.createElement("blockquote");
    q.className = "quote";
    const p = document.createElement("p");
    p.textContent = `“${d.texto}”`;
    const f = document.createElement("footer");
    f.textContent = d.cidade ? `${d.nome}, ${d.cidade}` : d.nome;
    q.append(p, f);
    box.append(q);
  });
  document.getElementById("depoimentos").hidden = false;
}

/* ---------- formulário de pedido ---------- */

const form = document.getElementById("pedido");
form?.addEventListener("submit", (e) => {
  e.preventDefault();
  const data = new FormData(form);
  const lines = ["Olá, Cassi Print! Vim pelo site e quero um orçamento.", "", `Tipo: ${data.get("tipo")}`];
  const ideia = String(data.get("ideia") || "").trim();
  const qtd = String(data.get("quantidade") || "").trim();
  const nome = String(data.get("nome") || "").trim();
  if (ideia) lines.push(`Ideia: ${ideia}`);
  if (qtd) lines.push(`Quantidade: ${qtd}`);
  if (nome) lines.push(`Nome: ${nome}`);
  const url = waLink(lines.join("\n"));
  const win = window.open(url, "_blank", "noopener");
  if (!win) window.location.href = url;
});

/* ---------- avisos ---------- */

const ICONS = {
  truck: '<path d="M3 7h11v9H3zM14 10h4l3 3v3h-7z"/><circle cx="7" cy="18" r="1.8"/><circle cx="17" cy="18" r="1.8"/>',
  paw: '<circle cx="12" cy="15.5" r="3.6"/><circle cx="6.5" cy="10.5" r="1.8"/><circle cx="10" cy="6.8" r="1.8"/><circle cx="14" cy="6.8" r="1.8"/><circle cx="17.5" cy="10.5" r="1.8"/>',
  gift: '<rect x="3.5" y="9" width="17" height="11" rx="1.5"/><path d="M2.5 9h19M12 9v11M12 9c-1.5-3-5-4-5.5-1.5C6 9.5 12 9 12 9zm0 0c1.5-3 5-4 5.5-1.5.5 2-5.5 1.5-5.5 1.5z"/>',
  chat: '<path d="M4 5h16v11H9l-5 4z"/>',
  layers: '<path d="M12 4l9 4.5-9 4.5-9-4.5z"/><path d="M3 13l9 4.5 9-4.5"/>',
};

const TIPS = [
  { icon: "truck", text: "Enviamos para todo o Brasil.", href: "#orcamento" },
  { icon: "paw", text: "Transforme a foto do seu pet em uma escultura.", wa: "Olá, Cassi Print! Quero uma escultura do meu pet." },
  { icon: "gift", text: "Presente único: personalizamos com nome e cores.", href: "#orcamento" },
  { icon: "chat", text: "Orçamento sem compromisso pelo WhatsApp.", wa: "Olá, Cassi Print! Vim pelo site e quero fazer um orçamento." },
  { icon: "layers", text: "Brindes personalizados para empresas e eventos.", wa: "Olá, Cassi Print! Quero brindes personalizados para a minha empresa ou evento." },
];

function startTips() {
  const toast = document.querySelector(".toast");
  if (!toast) return;
  const body = toast.querySelector(".toast__body");
  const icon = toast.querySelector(".toast__icon");
  const text = toast.querySelector(".toast__text");
  let index = 0;
  let stopped = false;
  let timer = 0;

  const hide = () => {
    toast.classList.remove("is-in");
    setTimeout(() => (toast.hidden = true), 500);
  };

  const show = () => {
    if (stopped) return;
    // Não interrompe quem está preenchendo o pedido
    if (form && form.contains(document.activeElement)) {
      timer = setTimeout(show, 6000);
      return;
    }
    const tip = TIPS[index % TIPS.length];
    index++;
    icon.innerHTML = `<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ICONS[tip.icon]}</svg>`;
    text.textContent = tip.text;
    if (tip.wa) {
      body.href = waLink(tip.wa);
      body.target = "_blank";
      body.rel = "noopener";
    } else {
      body.href = tip.href;
      body.removeAttribute("target");
    }
    toast.hidden = false;
    requestAnimationFrame(() => requestAnimationFrame(() => toast.classList.add("is-in")));
    timer = setTimeout(() => {
      hide();
      if (index < TIPS.length * 2) timer = setTimeout(show, 14000);
    }, 6500);
  };

  toast.querySelector(".toast__close").addEventListener("click", () => {
    stopped = true;
    clearTimeout(timer);
    hide();
  });
  body.addEventListener("click", (e) => {
    const href = body.getAttribute("href");
    if (href?.startsWith("#")) {
      e.preventDefault();
      const target = document.querySelector(href);
      if (lenis) lenis.scrollTo(target, { offset: -70, duration: 1.6 });
      else target?.scrollIntoView();
    }
    hide();
  });

  timer = setTimeout(show, 8000);
}
startTips();

/* ---------- impressora 3D da abertura ---------- */

const hero = document.querySelector(".hero");
const stage = document.querySelector(".hero__stage");
const canvas = document.querySelector(".hero__canvas");
const status = document.querySelector(".print-status");
const statusLabel = document.querySelector(".print-status__label");
const statusBar = document.querySelector(".print-status__bar");

const LAYERS = 240;
const BODY_H = 1.0; // altura do vaso
const EAR_H = 0.2;
const TOTAL_H = BODY_H + EAR_H - 0.02;
const EAR_R = 0.12;
const EAR_ANGLES = [Math.PI / 2 - 0.55, Math.PI / 2 + 0.55];
// O rostinho do gato fica virado para a câmera
const FACE = 0.8;

const clamp01 = (v) => Math.min(1, Math.max(0, v));
const smooth = (t) => t * t * (3 - 2 * t);
const lerp = (a, b, t) => a + (b - a) * t;
const radiusAt = (y) => 0.38 + 0.1 * Math.sin(clamp01(y / BODY_H) * Math.PI * 0.85);

function supportsWebGL() {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

function layerBump(n) {
  const c = document.createElement("canvas");
  c.width = 8;
  c.height = 2048;
  const g = c.getContext("2d");
  const step = c.height / n;
  for (let i = 0; i < n; i++) {
    const gr = g.createLinearGradient(0, i * step, 0, (i + 1) * step);
    gr.addColorStop(0, "#333");
    gr.addColorStop(0.5, "#fff");
    gr.addColorStop(1, "#333");
    g.fillStyle = gr;
    g.fillRect(0, i * step, c.width, step);
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

function plateTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 512;
  const g = c.getContext("2d");
  g.fillStyle = "#8a6a43";
  g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 9000; i++) {
    g.fillStyle = `rgba(${Math.random() < 0.5 ? "255,230,190" : "40,25,10"},${Math.random() * 0.08})`;
    g.fillRect(Math.random() * 512, Math.random() * 512, 2, 2);
  }
  g.strokeStyle = "rgba(30,20,10,0.25)";
  g.lineWidth = 2;
  for (let i = 1; i < 8; i++) {
    g.beginPath();
    g.moveTo(i * 64, 0);
    g.lineTo(i * 64, 512);
    g.moveTo(0, i * 64);
    g.lineTo(512, i * 64);
    g.stroke();
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function buildPrinter(renderer) {
  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.55;

  const key = new THREE.DirectionalLight("#fff3e4", 2.2);
  key.position.set(-2, 4, 3);
  key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024);
  Object.assign(key.shadow.camera, { left: -1.5, right: 1.5, top: 2, bottom: -1, near: 0.5, far: 10 });
  key.shadow.bias = -0.0005;
  scene.add(key);
  scene.add(new THREE.HemisphereLight("#dfe8ff", "#1a2238", 0.7));

  const clip = new THREE.Plane(new THREE.Vector3(0, -1, 0), 0);
  const bump = layerBump(LAYERS);
  bump.repeat.set(1, 1);

  // Peça impressa: vaso de gatinho
  const filament = new THREE.MeshStandardMaterial({
    color: "#ea7a52",
    roughness: 0.5,
    bumpMap: bump,
    bumpScale: 1.4,
    side: THREE.DoubleSide,
    clippingPlanes: [clip],
    clipShadows: true,
  });
  const piece = new THREE.Group();
  scene.add(piece);
  const profile = [];
  for (let i = 0; i <= 120; i++) {
    const y = (i / 120) * BODY_H;
    profile.push(new THREE.Vector2(radiusAt(y), y));
  }
  const body = new THREE.Mesh(new THREE.LatheGeometry(profile, 96), filament);
  body.castShadow = true;
  piece.add(body);
  const floorDisc = new THREE.Mesh(new THREE.CircleGeometry(radiusAt(0), 64), filament);
  floorDisc.rotation.x = -Math.PI / 2;
  floorDisc.position.y = 0.002;
  piece.add(floorDisc);

  EAR_ANGLES.forEach((a, i) => {
    const r = radiusAt(BODY_H) - 0.06;
    const ear = new THREE.Mesh(new THREE.ConeGeometry(EAR_R, EAR_H, 40, 1, false), filament);
    ear.position.set(r * Math.cos(a), BODY_H - 0.02 + EAR_H / 2, r * Math.sin(a));
    ear.rotation.z = (i === 0 ? -1 : 1) * 0.12;
    ear.castShadow = true;
    piece.add(ear);
  });

  // Rostinho: olhos fechados, nariz e bochechas
  const faceMat = (color) =>
    new THREE.MeshStandardMaterial({ color, roughness: 0.6, clippingPlanes: [clip] });
  const eyeMat = faceMat("#13203a");
  [-1, 1].forEach((s) => {
    const y = 0.62;
    const r = radiusAt(y);
    const x = 0.15 * s;
    const eye = new THREE.Mesh(new THREE.TorusGeometry(0.05, 0.011, 12, 32, Math.PI), eyeMat);
    eye.position.set(x, y, Math.sqrt(r * r - x * x) + 0.004);
    eye.rotation.y = Math.asin(x / r);
    piece.add(eye);
    const cheek = new THREE.Mesh(new THREE.SphereGeometry(0.045, 24, 12), faceMat("#f6a184"));
    const cy = 0.52;
    const cr = radiusAt(cy);
    const cx = 0.24 * s;
    cheek.position.set(cx, cy, Math.sqrt(cr * cr - cx * cx) - 0.012);
    cheek.scale.set(1, 0.7, 0.35);
    cheek.rotation.y = Math.asin(cx / cr);
    piece.add(cheek);
  });
  const nose = new THREE.Mesh(new THREE.SphereGeometry(0.03, 20, 12), faceMat("#13203a"));
  nose.position.set(0, 0.55, radiusAt(0.55) + 0.006);
  nose.scale.set(1.2, 0.8, 0.6);
  piece.add(nose);

  // Camada que acabou de sair do bico
  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(1, 0.012, 8, 120),
    new THREE.MeshBasicMaterial({ color: "#ffc070", toneMapped: false, transparent: true }),
  );
  ring.rotation.x = Math.PI / 2;
  scene.add(ring);

  // Impressora
  const steel = new THREE.MeshStandardMaterial({ color: "#3a4b6b", roughness: 0.45, metalness: 0.6 });
  const dark = new THREE.MeshStandardMaterial({ color: "#1c2740", roughness: 0.6, metalness: 0.3 });
  const bed = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.08, 1.6), dark);
  bed.position.y = -0.045;
  bed.receiveShadow = true;
  scene.add(bed);
  const plate = new THREE.Mesh(
    new THREE.BoxGeometry(1.6, 0.012, 1.4),
    new THREE.MeshStandardMaterial({ map: plateTexture(), roughness: 0.8, metalness: 0.2 }),
  );
  plate.position.y = -0.006;
  plate.receiveShadow = true;
  scene.add(plate);

  const POST_X = 1.02;
  const POST_Z = 0.82;
  const FRAME_H = 2.05;
  [-1, 1].forEach((sx) =>
    [-1, 1].forEach((sz) => {
      const post = new THREE.Mesh(new THREE.BoxGeometry(0.06, FRAME_H, 0.06), steel);
      post.position.set(sx * POST_X, FRAME_H / 2 - 0.08, sz * POST_Z);
      post.castShadow = true;
      scene.add(post);
    }),
  );
  [-1, 1].forEach((sz) => {
    const top = new THREE.Mesh(new THREE.BoxGeometry(POST_X * 2 + 0.06, 0.06, 0.06), steel);
    top.position.set(0, FRAME_H - 0.08, sz * POST_Z);
    scene.add(top);
  });

  const gantry = new THREE.Group();
  scene.add(gantry);
  const rails = [-1, 1].map((sx) => {
    const r = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.05, POST_Z * 2), steel);
    r.position.x = sx * POST_X;
    gantry.add(r);
    return r;
  });
  const xBar = new THREE.Mesh(new THREE.BoxGeometry(POST_X * 2, 0.045, 0.045), steel);
  gantry.add(xBar);

  const head = new THREE.Group();
  scene.add(head);
  const carriage = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.16, 0.14), dark);
  carriage.position.y = 0.3;
  carriage.castShadow = true;
  head.add(carriage);
  const fan = new THREE.Mesh(
    new THREE.CylinderGeometry(0.055, 0.055, 0.01, 32),
    new THREE.MeshStandardMaterial({ color: "#f2a541", roughness: 0.5 }),
  );
  fan.rotation.x = Math.PI / 2;
  fan.position.set(0, 0.3, 0.075);
  head.add(fan);
  const block = new THREE.Mesh(
    new THREE.BoxGeometry(0.08, 0.07, 0.08),
    new THREE.MeshStandardMaterial({ color: "#c9ced6", roughness: 0.3, metalness: 1 }),
  );
  block.position.y = 0.15;
  head.add(block);
  const nozzle = new THREE.Mesh(
    new THREE.ConeGeometry(0.035, 0.08, 24),
    new THREE.MeshStandardMaterial({ color: "#c9a25a", roughness: 0.25, metalness: 1 }),
  );
  nozzle.rotation.x = Math.PI;
  nozzle.position.y = 0.075;
  head.add(nozzle);
  const tip = new THREE.Mesh(
    new THREE.SphereGeometry(0.014, 16, 8),
    new THREE.MeshBasicMaterial({ color: "#ffd08a", toneMapped: false }),
  );
  tip.position.y = 0.03;
  head.add(tip);
  const glow = new THREE.PointLight("#ffb05c", 0.8, 0.9, 2);
  glow.position.y = 0.02;
  head.add(glow);

  return { scene, clip, piece, ring, gantry, xBar, rails, head, tip, glow };
}

async function startPrinter() {
  if (!canvas || !stage || !supportsWebGL()) return;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setClearColor(0x000000, 0);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.localClippingEnabled = true;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  const p = buildPrinter(renderer);
  const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 40);
  root.classList.add("has-3d");

  let fitDist = 6;
  function layout() {
    const r = stage.getBoundingClientRect();
    const w = Math.max(1, Math.round(r.width));
    const h = Math.max(1, Math.round(r.height));
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    const v = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
    fitDist = Math.max(3.1 / 2 / v, 3.0 / 2 / (v * camera.aspect));
  }
  layout();
  new ResizeObserver(layout).observe(stage);

  let visible = true;
  new IntersectionObserver(([e]) => (visible = e.isIntersecting)).observe(hero);

  const progress = () => {
    const r = hero.getBoundingClientRect();
    const run = r.height - window.innerHeight;
    return run > 0 ? clamp01(-r.top / run) : 1;
  };

  let current = progress();
  let parked = 0;
  let spin = 0;
  let lastTime = performance.now();
  let lastGoal = -1;
  const target = new THREE.Vector3(0, 0.78, 0);

  function frame(now) {
    requestAnimationFrame(frame);
    if (lenis) lenis.raf(now);
    const dt = Math.min(0.05, (now - lastTime) / 1000);
    lastTime = now;
    if (!visible) return;

    const goal = progress();
    // Sem animações contínuas, só redesenha quando a rolagem muda
    if (reduced && goal === lastGoal) return;
    lastGoal = goal;
    current = reduced ? goal : current + (goal - current) * 0.15;
    const printed = clamp01((current - 0.03) / 0.85);
    const done = printed >= 0.999;
    const h = Math.max(0.004, printed * TOTAL_H);
    const t = reduced ? 0 : now / 1000;

    p.clip.constant = h;
    parked += ((done ? 1 : 0) - parked) * Math.min(1, dt * 3);

    // Caminho do bico: contorno do vaso ou das orelhas
    let nx;
    let nz;
    if (h < BODY_H) {
      const r = radiusAt(h);
      const a = t * 2.4;
      nx = r * Math.cos(a);
      nz = r * Math.sin(a);
      p.ring.visible = !done;
      p.ring.position.y = h;
      p.ring.scale.set(r, r, 1);
    } else {
      const k = clamp01((h - (BODY_H - 0.02)) / EAR_H);
      const er = Math.max(0.01, EAR_R * (1 - k));
      const which = Math.floor(t / 0.7) % 2;
      const a0 = EAR_ANGLES[which] - FACE;
      const cr = radiusAt(BODY_H) - 0.06;
      const a = t * 6;
      nx = cr * Math.cos(a0) + er * Math.cos(a);
      nz = cr * Math.sin(a0) + er * Math.sin(a);
      p.ring.visible = false;
    }
    // Ao terminar, o cabeçote sobe e vai para o canto
    nx = lerp(nx, 0.75, parked);
    nz = lerp(nz, -0.55, parked);
    const hy = lerp(h, 1.55, parked);
    p.head.position.set(nx, hy, nz);
    p.gantry.position.set(0, hy + 0.3, 0);
    p.xBar.position.z = nz;
    p.tip.visible = parked < 0.5;
    p.glow.intensity = 0.8 * (1 - parked);
    p.ring.material.opacity = 0.9 + 0.1 * Math.sin(t * 12);

    // Peça pronta balança de leve, sempre olhando para quem está vendo
    if (done && !reduced) spin += dt;
    p.piece.rotation.y = FACE + Math.sin(spin * 0.8) * 0.35 * parked;

    const az = 0.45 + current * 0.45 + (reduced ? 0 : Math.sin(t * 0.25) * 0.06);
    const el = 0.42 - current * 0.12;
    const dist = fitDist;
    camera.position.set(
      target.x + dist * Math.sin(az) * Math.cos(el),
      target.y + dist * Math.sin(el),
      target.z + dist * Math.cos(az) * Math.cos(el),
    );
    camera.lookAt(target);
    renderer.render(p.scene, camera);

    // Status da impressão
    if (status) {
      const layer = Math.round(printed * LAYERS);
      statusBar.style.setProperty("--p", printed.toFixed(4));
      status.classList.toggle("is-done", done);
      statusLabel.textContent = done
        ? "Pronto! Agora imagine o seu."
        : printed < 0.004
          ? "Role para imprimir"
          : `Imprimindo camada ${layer} de ${LAYERS}`;
    }
  }
  requestAnimationFrame(frame);
}

if (!canvas || !supportsWebGL()) {
  // Sem 3D: só a rolagem suave
  const raf = (time) => {
    if (lenis) lenis.raf(time);
    requestAnimationFrame(raf);
  };
  requestAnimationFrame(raf);
} else {
  startPrinter();
}
