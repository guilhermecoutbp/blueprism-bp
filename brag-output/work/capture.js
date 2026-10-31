// Grava o site da Vellaro quadro a quadro. Cada quadro é função só do tempo:
// o relógio da página é falso e avança 1/30 s por quadro, as animações CSS
// são posicionadas à mão e a rolagem segue o roteiro do brag-plan.md.
// Uso: node capture.js <pasta-de-saida> <de (s)> <até (s)> [um a cada N quadros]
const { chromium } = require("playwright");
const fs = require("fs");

const URL = "http://localhost:8782/index.html";
const W = 1920;
const H = 1080;
const FPS = 30;
const DURATION = 20;
const INTRO_SPEED = 1.55; // a entrada do logo roda 1,55x mais rápida que no site

const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

function scrollAt(t, K, vh) {
  const ledHold = K[4] + 0.14 * vh;
  const pts = [
    [0, 0],
    [3.2, 0],
    [5.6, K[1]],
    [6.4, K[1]],
    [8.0, K[2]],
    [10.4, K[3]],
    [12.8, ledHold],
    [15.2, ledHold],
    [16.8, K[5]],
    [20.0, K[5]],
  ];
  for (let i = 0; i < pts.length - 1; i++) {
    const [t0, y0] = pts[i];
    const [t1, y1] = pts[i + 1];
    if (t <= t1) return y0 + (y1 - y0) * ease(Math.min(1, Math.max(0, (t - t0) / (t1 - t0))));
  }
  return pts[pts.length - 1][1];
}

(async () => {
  const out = process.argv[2];
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ args: ["--enable-unsafe-swiftshader", "--use-gl=angle", "--use-angle=swiftshader"] });
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.clock.install({ time: 0 });
  await page.goto(URL, { waitUntil: "networkidle" });
  // deixa fontes, cena 3D e marcos da rolagem prontos
  for (let i = 0; i < 40; i++) {
    await page.clock.runFor(100);
    const ready = await page.evaluate(() => document.documentElement.classList.contains("is-live") && document.fonts.status === "loaded");
    if (ready && i > 10) break;
  }
  await page.evaluate(() => document.fonts.ready);

  // Endereço do site para o fecho, no estilo da página
  await page.addStyleTag({
    content: `.brag-url{position:fixed;left:var(--gutter);bottom:64px;z-index:40;font-family:Jost,sans-serif;font-weight:300;
      font-size:1.35rem;letter-spacing:.14em;color:#d8d5d0;opacity:0;display:flex;align-items:center;gap:18px}
      .brag-url i{display:block;width:56px;height:1px;background:#f3c98b;box-shadow:0 0 10px 1px rgba(243,201,139,.6)}`,
  });
  await page.evaluate(() => {
    const d = document.createElement("div");
    d.className = "brag-url";
    d.innerHTML = "<i></i><span>vellarodesign.netlify.app</span>";
    document.body.appendChild(d);
    // animações CSS ficam paradas e são posicionadas a cada quadro
    window.__anims = document.getAnimations();
    window.__anims.forEach((a) => a.pause());
  });

  const { K, vh } = await page.evaluate(() => {
    const vh = innerHeight;
    const max = document.documentElement.scrollHeight - vh;
    const K = [0];
    document.querySelectorAll(".chapter__text").forEach((t) => {
      const r = t.closest(".chapter").getBoundingClientRect();
      K.push(Math.min(max, Math.max(0, scrollY + r.top + r.height / 2 - vh / 2)));
    });
    return { K, vh };
  });

  // Trecho a gravar: [de, até) em segundos. Começa 0,5 s antes para a rolagem
  // suavizada do site chegar ao mesmo estado de uma gravação contínua.
  const total = DURATION * FPS;
  const fromF = Math.round(parseFloat(process.argv[3] ?? 0) * FPS);
  const toF = Math.min(total, Math.round(parseFloat(process.argv[4] ?? DURATION) * FPS));
  const every = parseInt(process.argv[5] ?? "1", 10);
  const startF = Math.max(0, fromF - 15);
  await page.evaluate((y) => window.scrollTo(0, y), scrollAt(startF / FPS, K, vh));
  await page.clock.runFor(1000);
  let done = 0;
  for (let f = startF; f < toF; f++) {
    const t = f / FPS;
    const want = f >= fromF && (f - fromF) % every === 0;
    await page.evaluate(
      ({ t, y, speed }) => {
        window.__anims.forEach((a) => (a.currentTime = t * speed * 1000));
        window.scrollTo(0, y);
        const u = Math.min(1, Math.max(0, (t - 18.4) / 0.8));
        document.querySelector(".brag-url").style.opacity = String(u * u * (3 - 2 * u));
      },
      { t, y: scrollAt(t, K, vh), speed: INTRO_SPEED },
    );
    await page.clock.runFor(1000 / FPS);
    if (want) {
      await page.screenshot({ path: `${out}/${String(f).padStart(4, "0")}.jpg`, type: "jpeg", quality: 93, timeout: 300000 });
      done++;
      if (done % 15 === 0) console.log(`quadro ${f} (${t.toFixed(1)} s)`);
    }
  }
  console.log("pronto", done, "quadros", errors.length ? "erros: " + errors.join(" | ") : "sem erros");
  await browser.close();
})();
