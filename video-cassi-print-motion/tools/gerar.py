#!/usr/bin/env python3
"""Gera o projeto HyperFrames 'video-cassi-print-motion' (versão motion graphic)."""
import json, math, os, sys

P = sys.argv[1]
os.makedirs(f"{P}/compositions", exist_ok=True)

ACC, NAVY, INK, BLUE = "#e78d33", "#1a2530", "#f7f3ec", "#45839a"

# ---------------------------------------------------------------- etapas (cartões)
# id, início no filme, duração, vídeos [(id, início local, duração, fonte, velocidade, object-position)],
# legendas [(início, saída|None, linha1, destaque)], punch-ins [(t, escala, origem)]
PASSOS = [
    ("passo-1", 2.8, 2.4, [("v-pecas", 0, 2.4, 2.9, 1.0, "50% 62%")],
     [(0.3, None, "Peça por", "peça.")], [(1.2, 1.1, "50% 45%")]),
    ("passo-2", 5.2, 2.4, [("v-rosto", 0, 2.4, 6.4, 1.6, "50% 55%")],
     [(0.3, None, "Encaixe a", "encaixe.")], [(1.2, 1.12, "50% 40%")]),
    ("passo-3", 7.6, 2.0, [("v-chapeu", 0, 2.0, 11.0, 1.2, "50% 45%")],
     [(0.3, None, "Chapéu de", "marinheiro.")], [(1.2, 1.1, "50% 40%")]),
    ("passo-4", 9.6, 2.4, [("v-dentes", 0, 2.4, 13.85, 1.0, "50% 85%")],
     [(0.3, None, "Olha esses", "dentes!")], [(1.2, 1.14, "50% 57%")]),
    ("passo-5", 12.0, 2.4, [("v-bracos", 0, 2.4, 21.3, 0.9, "50% 50%")],
     [(0.3, None, "Braços no", "lugar.")], [(1.2, 1.1, "50% 45%")]),
    ("passo-6", 14.4, 5.2, [("v-base", 0, 1.6, 24.65, 1.1, "50% 55%"),
                            ("v-barco", 1.6, 3.6, 26.5, 0.83, "50% 55%")],
     [(0.3, 1.42, "A base no", "barco."), (2.0, None, "Pronto pra", "zarpar!")],
     [(1.6, 1.0, "50% 50%"), (3.6, 1.1, "50% 45%")]),
]

def legenda_html(pid, i, l1, dest):
    w1 = "".join(f'<span class="pal">{w}</span> ' for w in l1.split())
    return (f'      <div id="{pid}-leg{i}" class="legenda">\n'
            f'        <div class="linha">{w1.strip()}</div>\n'
            f'        <div class="linha"><span class="marca"><span class="tarja"></span><span class="pal txt">{dest}</span></span></div>\n'
            f'      </div>\n')

CARD_CSS = f"""
    #root {{ position: absolute; inset: 0; overflow: hidden; font-family: var(--font-display, "Nunito"), sans-serif; }}
    .cartao {{ position: absolute; left: 90px; top: 340px; width: 900px; height: 980px; border-radius: 44px; overflow: hidden;
      background: #0f171f; box-shadow: 0 34px 80px rgba(0, 0, 0, 0.5); }}
    .lente {{ position: absolute; left: 0; top: 0; width: 900px; height: 980px; }}
    .lente video {{ position: absolute; left: 0; top: 0; width: 900px; height: 980px; object-fit: cover; }}
    .escurece {{ position: absolute; left: 0; top: 600px; width: 900px; height: 380px;
      background: linear-gradient(to bottom, rgba(26, 37, 48, 0) 0%, rgba(26, 37, 48, 0.82) 100%); }}
    .moldura {{ position: absolute; inset: 0; border-radius: 44px; border: 7px solid var(--color-accent, {ACC}); }}
    .legenda {{ position: absolute; left: 136px; top: 1070px; width: 820px; color: var(--color-ink, {INK});
      font-weight: 900; font-size: 100px; line-height: 1.02; letter-spacing: -0.02em; text-transform: uppercase; }}
    .legenda .linha {{ display: block; white-space: nowrap; }}
    .legenda .pal {{ display: inline-block; }}
    .legenda .marca {{ position: relative; display: inline-block; padding: 0 20px 6px; margin-left: -20px; }}
    .legenda .tarja {{ position: absolute; left: 0; top: 8px; right: 0; bottom: 0; border-radius: 16px;
      background: var(--color-accent, {ACC}); }}
    .legenda .txt {{ position: relative; color: var(--color-ground, {NAVY}); }}
"""

def passo_html(pid, dur, videos, legendas, punches, extra_html="", extra_css="", extra_js=""):
    vids = ""
    for vid, st, d, src, rate, pos in videos:
        vids += (f'          <video id="{vid}" class="clip" src="assets/montagem.mp4" data-start="{st}" data-duration="{d}" '
                 f'data-media-start="{src}" data-playback-rate="{rate}" data-track-index="0" muted playsinline '
                 f'style="object-position: {pos}"></video>\n')
    legs = "".join(legenda_html(pid, i + 1, l1, dest) for i, (_, _, l1, dest) in enumerate(legendas))
    js = ""
    for t, s, o in punches:
        js += f'      tl.set("#{pid}-lente", {{ scale: {s}, transformOrigin: "{o}" }}, {t});\n'
    for i, (ent, sai, _, _) in enumerate(legendas):
        sel = f"#{pid}-leg{i+1}"
        js += (f'      tl.fromTo("{sel} .pal", {{ opacity: 0, scale: 1.7, filter: "blur(10px)" }}, '
               f'{{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.22, ease: "expo.out", stagger: 0.08 }}, {ent});\n')
        js += (f'      tl.fromTo("{sel} .tarja", {{ scaleX: 0, transformOrigin: "0% 50%" }}, '
               f'{{ scaleX: 1, duration: 0.3, ease: "expo.out" }}, {round(ent + 0.12, 2)});\n')
        if sai is not None:
            js += (f'      tl.to("{sel} .pal, {sel} .tarja", {{ opacity: 0, filter: "blur(10px)", xPercent: -8, '
                   f'duration: 0.18, ease: "power3.in", stagger: 0.03 }}, {sai});\n')
        else:
            pass
    return f"""<template>
  <style>{CARD_CSS}{extra_css}  </style>
  <div id="root" data-composition-id="{pid}" data-width="1080" data-height="1920">
    <div id="{pid}-cartao" class="cartao">
      <div id="{pid}-lente" class="lente" data-layout-allow-overflow>
{vids}{extra_html}      </div>
      <div class="escurece"></div>
      <div class="moldura"></div>
    </div>
{legs}  </div>
  <script>
    (() => {{
      const tl = gsap.timeline({{ paused: true }});
{js}{extra_js}      tl.set({{}}, {{}}, {dur});
      window.__timelines["{pid}"] = tl;
    }})();
  </script>
</template>
"""

# passo-4: círculo desenhado à mão em volta dos dentes + seta
CALLOUT_HTML = """        <svg id="passo-4-rabisco" class="rabisco" width="900" height="980" viewBox="0 0 900 980">
          <path id="passo-4-circulo" d="M 210 560 C 260 450, 760 440, 805 555 C 845 670, 560 705, 410 680 C 250 650, 205 590, 275 505" />
        </svg>
"""
CALLOUT_CSS = f"""
    .rabisco {{ position: absolute; left: 0; top: 0; overflow: visible; }}
    .rabisco path {{ fill: none; stroke: var(--color-accent, {ACC}); stroke-width: 14; stroke-linecap: round; stroke-linejoin: round;
      filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.35)); }}
"""
CALLOUT_JS = """      const circ = document.querySelector("#passo-4-circulo");
      const L = circ.getTotalLength();
      tl.fromTo(circ, { strokeDasharray: L, strokeDashoffset: L }, { strokeDashoffset: 0, duration: 0.5, ease: "power2.inOut" }, 0.55);
"""

for pid, st, dur, videos, legendas, punches in PASSOS:
    kw = {}
    if pid == "passo-4":
        kw = dict(extra_html=CALLOUT_HTML, extra_css=CALLOUT_CSS, extra_js=CALLOUT_JS)
    open(f"{P}/compositions/{pid}.html", "w").write(passo_html(pid, dur, videos, legendas, punches, **kw))

# ---------------------------------------------------------------- abertura
ABERTURA = f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; font-family: var(--font-display, "Nunito"), sans-serif; }}
    #abertura-kicker {{ position: absolute; left: 0; top: 176px; width: 1080px; text-align: center; }}
    #abertura-kicker .pilula {{ display: inline-block; padding: 14px 30px 16px; border-radius: 999px; background: var(--color-ground, {NAVY});
      color: var(--color-ink, {INK}); font-weight: 800; font-size: 38px; letter-spacing: 0.04em; }}
    #abertura-titulo {{ position: absolute; left: 0; top: 252px; width: 1080px; text-align: center; font-weight: 900; font-size: 118px;
      line-height: 0.96; letter-spacing: -0.02em; color: var(--color-ground, {NAVY}); text-transform: uppercase;
      text-shadow: 0 0 28px rgba(247, 243, 236, 0.95), 0 0 10px rgba(247, 243, 236, 0.85); }}
    #abertura-titulo span {{ display: inline-block; }}
    #abertura-titulo .acento {{ color: var(--color-accent, {ACC}); background: var(--color-ground, {NAVY}); border-radius: 18px;
      padding: 0 22px 4px; margin-left: 6px; text-shadow: none; }}
    #abertura-selo {{ position: absolute; left: 742px; top: 560px; width: 250px; height: 250px; }}
    #abertura-selo .disco {{ position: absolute; inset: 0; border-radius: 50%; background: var(--color-accent, {ACC});
      box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35); }}
    #abertura-selo .anel {{ position: absolute; inset: 14px; border-radius: 50%; border: 4px dashed rgba(26, 37, 48, 0.55); }}
    #abertura-selo .texto {{ position: absolute; left: 0; top: 66px; width: 250px; text-align: center; color: var(--color-ground, {NAVY});
      font-weight: 900; font-size: 52px; line-height: 0.98; text-transform: uppercase; z-index: 2; }}
  </style>
  <div id="root" data-composition-id="abertura" data-width="1080" data-height="1920"
    data-composition-variables='[{{"id":"kicker","type":"string","label":"Selo do topo","default":"do filamento à estante"}}]'>
    <div id="abertura-kicker" class="clip" data-start="0" data-duration="2.8">
      <div class="pilula"><span data-var-text="kicker">do filamento à estante</span></div>
    </div>
    <div id="abertura-titulo" class="clip" data-start="0" data-duration="2.8">
      <span>Impresso</span><br /><span>em</span> <span class="acento">3D</span>
    </div>
    <div id="abertura-selo" class="clip" data-start="0.8" data-duration="2">
      <div id="abertura-selo-mov" style="position:absolute;inset:0">
        <div class="disco"></div><div class="anel"></div>
        <div class="texto" data-layout-allow-occlusion>Feito<br />à mão</div>
      </div>
    </div>
  </div>
  <script>
    (() => {{
      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#abertura-kicker .pilula", {{ opacity: 0, scale: 0.9, filter: "blur(6px)" }},
        {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.35, ease: "back.out(1.6)" }}, 0.38);
      // o selo é carimbado na batida: cai grande e girado, assenta inclinado
      tl.fromTo("#abertura-selo-mov", {{ opacity: 0, scale: 1.9, rotation: -38 }},
        {{ opacity: 1, scale: 1, rotation: -12, duration: 0.32, ease: "back.out(1.6)" }}, 0.8);
      // punch no título na batida seguinte (o título não flutua: um golpe e para)
      tl.fromTo("#abertura-titulo", {{ scale: 1.06 }}, {{ scale: 1, duration: 0.3, ease: "expo.out" }}, 1.6);
      tl.set({{}}, {{}}, 2.8);
      window.__timelines["abertura"] = tl;
    }})();
  </script>
</template>
"""
open(f"{P}/compositions/abertura.html", "w").write(ABERTURA)

# ---------------------------------------------------------------- HUD (painel da impressora)
NOMES = ["As peças", "O rosto", "O chapéu", "Os detalhes", "Os braços", "O barco", "Pronto!"]
TROCAS = [2.4, 4.8, 6.8, 9.2, 11.6, 16.4]          # tempos locais (filme - 2.8)
FIM_HUD = 16.8                                       # 2.8 → 19.6
nomes_html = "".join(f'<div class="item">{n}</div>' for n in NOMES)
nums_html = "".join(f'<div class="item">{i:02d}</div>' for i in range(1, 7)) + '<div class="item">06</div>'
segs = [0] + TROCAS  # início de cada passo
prog_js = ""
for i in range(6):
    a, b = segs[i], segs[i + 1]
    prog_js += (f'      tl.fromTo("#hud-barra", {{ scaleX: {i/6:.4f} }}, {{ scaleX: {(i+1)/6:.4f}, duration: {round(b-a-0.02,2)}, ease: "none", immediateRender: false }}, {a});\n'
                f'      tl.fromTo(pct, {{ v: {100*i/6:.3f} }}, {{ v: {100*(i+1)/6:.3f}, duration: {round(b-a-0.02,2)}, ease: "none", immediateRender: false, onUpdate: mostra }}, {a});\n')
roll_js = ""
for k, t in enumerate(TROCAS):
    roll_js += (f'      tl.to("#hud-nomes", {{ y: {-(k+1)*74}, duration: 0.42, ease: "power4.out" }}, {t});\n'
                f'      tl.to("#hud-nums", {{ y: {-(k+1)*74}, duration: 0.42, ease: "power4.out" }}, {t});\n')
HUD = f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; font-family: var(--font-display, "Nunito"), sans-serif; }}
    #hud-painel {{ position: absolute; left: 90px; top: 182px; width: 900px; height: 132px; border-radius: 30px;
      background: #22303d; border: 3px solid rgba(231, 141, 51, 0.6); box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35); }}
    #hud-rotulo {{ position: absolute; left: 34px; top: 10px; color: var(--color-accent, {ACC}); font-weight: 800; font-size: 28px; line-height: 34px; letter-spacing: 0.14em; }}
    .janela {{ position: absolute; overflow: hidden; height: 74px; }}
    .janela .item {{ height: 74px; line-height: 74px; white-space: nowrap; }}
    #hud-jnum {{ left: 32px; top: 46px; width: 110px; }}
    #hud-nums {{ color: var(--color-ink, {INK}); font-weight: 900; font-size: 62px; }}
    #hud-div {{ position: absolute; left: 150px; top: 24px; width: 3px; height: 72px; background: rgba(247, 243, 236, 0.18); }}
    #hud-jnome {{ left: 178px; top: 24px; width: 540px; }}
    #hud-nomes {{ color: var(--color-ink, {INK}); font-weight: 900; font-size: 60px; letter-spacing: -0.01em; }}
    #hud-pct {{ position: absolute; right: 34px; top: 30px; width: 170px; text-align: right; color: var(--color-accent, {ACC});
      font-weight: 900; font-size: 52px; font-variant-numeric: tabular-nums; }}
    #hud-trilho {{ position: absolute; left: 178px; right: 34px; bottom: 18px; height: 10px; border-radius: 5px; background: rgba(247, 243, 236, 0.14); overflow: hidden; }}
    #hud-barra {{ position: absolute; left: 0; top: 0; width: 100%; height: 10px; border-radius: 5px; background: var(--color-accent, {ACC}); }}
  </style>
  <div id="root" data-composition-id="hud" data-width="1080" data-height="1920">
    <div id="hud-painel" class="clip" data-start="0" data-duration="{FIM_HUD}">
      <div id="hud-rotulo">PASSO</div>
      <div id="hud-jnum" class="janela" data-layout-ignore><div id="hud-nums">{nums_html}</div></div>
      <div id="hud-div"></div>
      <div id="hud-jnome" class="janela" data-layout-ignore><div id="hud-nomes">{nomes_html}</div></div>
      <div id="hud-pct">0%</div>
      <div id="hud-trilho"><div id="hud-barra"></div></div>
    </div>
  </div>
  <script>
    (() => {{
      const tl = gsap.timeline({{ paused: true }});
      const pctEl = document.querySelector("#hud-pct");
      const pct = {{ v: 0 }};
      const mostra = () => {{ pctEl.textContent = Math.round(pct.v) + "%"; }};
      // entra junto com o primeiro cartão, na corrente (para a esquerda)
      tl.fromTo("#hud-painel", {{ xPercent: 12, opacity: 0.35 }}, {{ xPercent: 0, opacity: 1, duration: 0.42, ease: "power4.out" }}, 0);
      tl.set("#hud-barra", {{ scaleX: 0, transformOrigin: "0% 50%" }}, 0);
      // a barra e a porcentagem avançam passo a passo; o nome e o número rolam a cada corte
{prog_js}{roll_js}      tl.fromTo("#hud-painel", {{ borderColor: "rgba(231, 141, 51, 0.6)" }}, {{ borderColor: "rgba(231, 141, 51, 1)", duration: 0.3, ease: "power2.out" }}, 16.4);
      // sai para cima junto com o corte de elevação (a conclusão sobe)
      tl.to("#hud-painel", {{ yPercent: -120, opacity: 0, duration: 0.34, ease: "power3.in" }}, {round(FIM_HUD-0.34,2)});
      tl.set({{}}, {{}}, {FIM_HUD});
      window.__timelines["hud"] = tl;
    }})();
  </script>
</template>
"""
open(f"{P}/compositions/hud.html", "w").write(HUD)

# ---------------------------------------------------------------- fundo animado
SEAMS_ESQ = [2.8, 5.2, 7.6, 9.6, 12.0, 14.4]
mov_js = ""
for k, t in enumerate(SEAMS_ESQ):
    mov_js += (f'      tl.to("#fundo-faixa1", {{ x: {-(k+1)*300}, duration: 0.76, ease: "power2.inOut" }}, {round(t-0.34,2)});\n'
               f'      tl.to("#fundo-faixa2", {{ x: {-(k+1)*460}, duration: 0.76, ease: "power2.inOut" }}, {round(t-0.34,2)});\n')
FUNDO = f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; font-family: var(--font-display, "Nunito"), sans-serif; }}
    #fundo-chao {{ position: absolute; inset: 0; background: var(--color-ground, {NAVY}); }}
    #fundo-camadas {{ position: absolute; inset: 0;
      background: repeating-linear-gradient(to bottom, rgba(247, 243, 236, 0.07) 0px, rgba(247, 243, 236, 0.07) 2px, rgba(247, 243, 236, 0) 2px, rgba(247, 243, 236, 0) 16px); }}
    #fundo-brilho {{ position: absolute; left: -60px; top: 260px; width: 1200px; height: 1200px;
      background: radial-gradient(circle at 50% 50%, rgba(69, 131, 154, 0.42) 0%, rgba(69, 131, 154, 0) 62%); }}
    #fundo-faixas {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }}
    .faixa {{ position: absolute; left: 0; white-space: nowrap; font-weight: 900; text-transform: uppercase; letter-spacing: -0.01em; }}
    #fundo-faixa1 {{ top: 1400px; font-size: 200px; color: transparent; -webkit-text-stroke: 3px rgba(231, 141, 51, 0.6); }}
    #fundo-faixa2 {{ top: 1640px; font-size: 104px; color: rgba(247, 243, 236, 0.2); }}
  </style>
  <div id="root" data-composition-id="fundo" data-width="1080" data-height="1920">
    <div id="fundo-chao" class="clip" data-start="0" data-duration="28.4"></div>
    <div id="fundo-camadas" class="clip" data-start="0" data-duration="28.4"></div>
    <div id="fundo-brilho" class="clip" data-start="0" data-duration="28.4"></div>
    <div id="fundo-faixas" class="clip" data-start="0" data-duration="28.4" data-layout-allow-overflow>
      <div id="fundo-faixa1" class="faixa" data-layout-ignore>{"Impresso em 3D • Cassi Print • " * 6}</div>
      <div id="fundo-faixa2" class="faixa" data-layout-ignore>{"Peça por peça • Encaixe a encaixe • " * 6}</div>
    </div>
  </div>
  <script>
    (() => {{
      const tl = gsap.timeline({{ paused: true }});
      // as faixas só andam nos cortes, na mesma direção dos cartões: a câmera indo para a esquerda
{mov_js}      tl.set({{}}, {{}}, 28.4);
      window.__timelines["fundo"] = tl;
    }})();
  </script>
</template>
"""
open(f"{P}/compositions/fundo.html", "w").write(FUNDO)

# ---------------------------------------------------------------- payoff: a peça pronta
def rnd(seed):
    x = math.sin(seed * 12.9898) * 43758.5453
    return x - math.floor(x)
raios = ""
N = 18
for i in range(N):
    a0, a1 = (i / N) * 2 * math.pi, ((i + 0.5) / N) * 2 * math.pi
    R = 1300
    p = f"M 0 0 L {R*math.cos(a0):.1f} {R*math.sin(a0):.1f} L {R*math.cos(a1):.1f} {R*math.sin(a1):.1f} Z"
    cor = "rgba(231,141,51,0.20)" if i % 2 == 0 else "rgba(69,131,154,0.30)"
    raios += f'<path d="{p}" fill="{cor}" />'
CORES = [ACC, BLUE, INK, "#f3a6c0", "#3fbf5a"]
conf_html, conf_js = "", ""
for i in range(22):
    ang = (i / 22) * 2 * math.pi + rnd(i + 1) * 0.5
    dist = 330 + rnd(i + 7) * 260
    dx, dy = math.cos(ang) * dist, math.sin(ang) * dist * 0.85 - 120
    rot = (rnd(i + 3) - 0.5) * 720
    w, h = (26 + int(rnd(i + 5) * 18), 12 + int(rnd(i + 9) * 8))
    conf_html += (f'      <div id="peca-conf-{i}" class="conf" style="width:{w}px;height:{h}px;background:{CORES[i % 5]}"></div>\n')
    conf_js += (f'      tl.fromTo("#peca-conf-{i}", {{ x: 0, y: 0, rotation: 0, opacity: 1, scale: 0.4 }}, '
                f'{{ x: {dx:.0f}, y: {dy:.0f}, rotation: {rot:.0f}, scale: 1, duration: 0.7, ease: "power3.out" }}, 0.12);\n'
                f'      tl.to("#peca-conf-{i}", {{ y: {dy+260:.0f}, opacity: 0, duration: 0.9, ease: "power2.in" }}, 0.82);\n')
PECA = f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; font-family: var(--font-display, "Nunito"), sans-serif; }}
    #peca-raios {{ position: absolute; left: 540px; top: 760px; width: 0; height: 0; }}
    #peca-raios svg {{ position: absolute; left: -1300px; top: -1300px; overflow: visible; }}
    #peca-luz {{ position: absolute; left: 90px; top: 310px; width: 900px; height: 900px;
      background: radial-gradient(circle at 50% 50%, rgba(247, 243, 236, 0.22) 0%, rgba(247, 243, 236, 0) 60%); }}
    #peca-figura {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; transform: translate(113px, -190px) scale(1.04); }}
    #peca-figura-mov {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }}
    #peca-sombra {{ position: absolute; left: 250px; top: 1280px; width: 420px; height: 90px; border-radius: 50%;
      background: radial-gradient(ellipse 50% 50% at 50% 50%, rgba(0, 0, 0, 0.55) 0%, rgba(0, 0, 0, 0) 100%); }}
    #peca-img {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
    #peca-confete {{ position: absolute; left: 540px; top: 760px; width: 0; height: 0; }}
    .conf {{ position: absolute; left: 0; top: 0; border-radius: 4px; }}
    #peca-frase {{ position: absolute; left: 0; top: 1110px; width: 1080px; text-align: center; color: var(--color-ink, {INK});
      font-weight: 900; font-size: 96px; line-height: 1.04; letter-spacing: -0.015em; text-transform: uppercase; }}
    #peca-frase .pal {{ display: inline-block; }}
    #peca-frase .marca {{ position: relative; display: inline-block; padding: 0 18px 6px; }}
    #peca-frase .tarja {{ position: absolute; left: 0; top: 8px; right: 0; bottom: 0; border-radius: 16px; background: var(--color-accent, {ACC}); }}
    #peca-frase .txt {{ position: relative; color: var(--color-ground, {NAVY}); }}
  </style>
  <div id="root" data-composition-id="peca" data-width="1080" data-height="1920">
    <div id="peca-raios" class="clip" data-start="0" data-duration="4" data-layout-allow-overflow>
      <svg id="peca-raios-svg" width="2600" height="2600" viewBox="-1300 -1300 2600 2600">{raios}</svg>
    </div>
    <div id="peca-luz" class="clip" data-start="0" data-duration="4"></div>
    <div id="peca-figura" class="clip" data-start="0" data-duration="4">
      <div id="peca-figura-mov">
        <div id="peca-sombra"></div>
        <img id="peca-img" src="assets/peca-recorte.png" alt="Figura montada no barco" />
      </div>
    </div>
    <div id="peca-confete" class="clip" data-start="0" data-duration="2" data-layout-allow-overflow>
{conf_html}    </div>
    <div id="peca-frase" class="clip" data-start="0.45" data-duration="3.55">
      <span class="pal">Feito</span> <span class="pal">em</span> <span class="marca"><span class="tarja"></span><span class="pal txt">3D.</span></span><br />
      <span class="pal">Montado</span> <span class="pal">à</span> <span class="pal">mão.</span>
    </div>
  </div>
  <script>
    (() => {{
      const tl = gsap.timeline({{ paused: true }});
      // a peça sobe junto com o corte para cima e assenta; os raios explodem uma vez e desaceleram até parar
      tl.fromTo("#peca-figura-mov", {{ y: 90 }}, {{ y: 0, duration: 0.6, ease: "expo.out" }}, 0);
      tl.fromTo("#peca-raios-svg", {{ scale: 0.2, rotation: -20, opacity: 0 }}, {{ scale: 1, rotation: 0, opacity: 1, duration: 0.7, ease: "expo.out" }}, 0);
      tl.to("#peca-raios-svg", {{ rotation: 24, duration: 3.2, ease: "power2.out" }}, 0.7);
      tl.fromTo("#peca-luz", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: "power2.out" }}, 0);
      tl.fromTo("#peca-sombra", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: "power2.out" }}, 0.2);
{conf_js}      tl.fromTo("#peca-frase .pal", {{ opacity: 0, scale: 1.7, filter: "blur(10px)" }}, {{ opacity: 1, scale: 1, filter: "blur(0px)", duration: 0.22, ease: "expo.out", stagger: 0.08 }}, 0.5);
      tl.fromTo("#peca-frase .tarja", {{ scaleX: 0, transformOrigin: "0% 50%" }}, {{ scaleX: 1, duration: 0.3, ease: "expo.out" }}, 0.66);
      tl.set({{}}, {{}}, 4);
      window.__timelines["peca"] = tl;
    }})();
  </script>
</template>
"""
open(f"{P}/compositions/peca.html", "w").write(PECA)

# ---------------------------------------------------------------- card final: logo
LOGO = f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; font-family: var(--font-display, "Nunito"), sans-serif; }}
    #logo-papel {{ position: absolute; left: -200px; top: -200px; width: 1480px; height: 2320px; background: var(--color-ink, {INK}); }}
    #logo-camadas {{ position: absolute; left: 0; top: 1360px; width: 1080px; height: 560px;
      background: repeating-linear-gradient(to bottom, rgba(231, 141, 51, 0.16) 0px, rgba(231, 141, 51, 0.16) 4px, rgba(231, 141, 51, 0) 4px, rgba(231, 141, 51, 0) 18px); }}
    #logo-marca {{ position: absolute; left: 160px; top: 300px; width: 760px; height: 784px; }}
    #logo-img {{ position: absolute; left: 0; top: 0; width: 760px; height: 784px; object-fit: contain; }}
    #logo-cta {{ position: absolute; left: 0; top: 1140px; width: 1080px; text-align: center; }}
    #logo-cta .pilula {{ display: inline-block; padding: 22px 52px 28px; border-radius: 999px; background: var(--color-ground, {NAVY});
      color: var(--color-ink, {INK}); font-weight: 900; font-size: 64px; line-height: 1; }}
    #logo-cta .apoio {{ margin-top: 26px; color: var(--color-ground, {NAVY}); font-weight: 800; font-size: 40px; letter-spacing: 0.02em; }}
  </style>
  <div id="root" data-composition-id="logo" data-width="1080" data-height="1920"
    data-composition-variables='[{{"id":"cta","type":"string","label":"Chamada","default":"Encomende já a sua"}},{{"id":"cta-apoio","type":"string","label":"Linha de apoio","default":"chame a gente no direct"}}]'>
    <div id="logo-papel" class="clip" data-start="0" data-duration="4.8" data-layout-allow-overflow></div>
    <div id="logo-camadas" class="clip" data-start="0" data-duration="4.8"></div>
    <div id="logo-marca" class="clip" data-start="0" data-duration="4.8">
      <img id="logo-img" src="assets/logo.png" alt="Cassi Print — Decoração e utensílios 3D" />
    </div>
    <div id="logo-cta" class="clip" data-start="0.9" data-duration="3.9">
      <div class="pilula" data-var-text="cta">Encomende já a sua</div>
      <div class="apoio" data-var-text="cta-apoio">chame a gente no direct</div>
    </div>
  </div>
  <script>
    (() => {{
      const tl = gsap.timeline({{ paused: true }});
      // as camadas laranja sobem por baixo (o card "termina de imprimir"), depois a chamada
      tl.fromTo("#logo-camadas", {{ clipPath: "inset(100% 0% 0% 0%)" }}, {{ clipPath: "inset(0% 0% 0% 0%)", duration: 0.7, ease: "steps(10)" }}, 0.2);
      tl.fromTo("#logo-cta .pilula", {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(1.7)" }}, 0.95);
      tl.fromTo("#logo-cta .apoio", {{ opacity: 0, filter: "blur(6px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.2, ease: "power2.out" }}, 1.2);
      tl.set({{}}, {{}}, 4.8);
      window.__timelines["logo"] = tl;
    }})();
  </script>
</template>
"""
open(f"{P}/compositions/logo.html", "w").write(LOGO)

# ---------------------------------------------------------------- index (raiz)
def host(id_, start, dur, track, z=None):
    return (f'        <div id="{id_}" class="clip" data-composition-id="{id_}" data-composition-src="compositions/{id_}.html" '
            f'data-start="{start}" data-duration="{dur}" data-track-index="{track}" data-track-kind="graphics"></div>\n')

cenas = ""
for k, (pid, st, dur, *_r) in enumerate(PASSOS):
    cenas += f'      <div id="cena-{k+1}" class="cena">\n{host(pid, st, dur, 3)}      </div>\n'

AUD = [
    # id, arquivo, início, duração, volume, extras
    ("trilha", "trilha.mp3", 0, 28.4, 0.85, 'data-media-start="0" data-fade-out="1.4"'),
    ("sfx-selo", "sfx/pop.mp3", 0.71, 0.6, 0.5, ""),
    ("sfx-corte1", "sfx/whoosh-short.mp3", 2.67, 0.57, 0.4, ""),
    ("sfx-corte2", "sfx/whoosh-cinematic.mp3", 4.93, 0.8, 0.32, 'data-media-start="2.2" data-fade-out="0.3"'),
    ("sfx-corte3", "sfx/whoosh-short.mp3", 7.43, 0.65, 0.34, 'data-playback-rate="0.8"'),
    ("sfx-corte4", "sfx/whoosh-short.mp3", 9.47, 0.57, 0.4, ""),
    ("sfx-rabisco", "sfx/click-soft.mp3", 10.11, 0.37, 0.5, ""),
    ("sfx-corte5", "sfx/whoosh-cinematic.mp3", 11.73, 0.8, 0.32, 'data-media-start="2.2" data-fade-out="0.3"'),
    ("sfx-corte6", "sfx/whoosh-short.mp3", 14.23, 0.65, 0.34, 'data-playback-rate="0.8"'),
    ("sfx-riser", "sfx/riser.mp3", 16.16, 3.5, 0.3, 'data-media-start="0" data-fade-in="1" data-fade-out="0.1"'),
    ("sfx-impacto", "sfx/impact-bass-1.mp3", 19.56, 2.1, 0.6, ""),
    ("sfx-logo", "sfx/impact-bass-2.mp3", 23.6, 1.2, 0.35, 'data-fade-out="0.4"'),
    ("sfx-cta", "sfx/pop.mp3", 24.43, 0.6, 0.45, ""),
]
auds = ""
for i, (id_, f, st, d, vol, ex) in enumerate(AUD):
    auds += (f'      <audio id="{id_}" class="clip" src="assets/{f}" data-start="{st}" data-duration="{d}" '
             f'data-volume="{vol}" data-track-index="{10+i}" {ex}></audio>\n')

INDEX = f"""<!doctype html>
<html
  lang="pt-BR"
  data-resolution="portrait"
  data-composition-variables='[
    {{"id":"color-ground","type":"color","label":"Fundo","default":"{NAVY}"}},
    {{"id":"color-ink","type":"color","label":"Texto","default":"{INK}"}},
    {{"id":"color-accent","type":"color","label":"Destaque (filamento)","default":"{ACC}"}},
    {{"id":"color-blue","type":"color","label":"Azul da marca","default":"{BLUE}"}},
    {{"id":"font-display","type":"string","label":"Fonte","default":"Nunito"}}
  ]'
>
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      :root {{ --color-ground: {NAVY}; --color-ink: {INK}; --color-accent: {ACC}; --color-blue: {BLUE}; --font-display: "Nunito"; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1080px; height: 1920px; overflow: hidden; background: var(--color-ground); }}
      #root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; font-family: var(--font-display), sans-serif; }}
      .cena {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }}
      #fundo-host {{ z-index: 1; }}
      #cena-gancho {{ z-index: 2; overflow: hidden; }}
      #cena-1, #cena-2, #cena-3, #cena-4, #cena-5, #cena-6 {{ z-index: 3; }}
      #cena-peca {{ z-index: 4; }}
      #hud-host {{ z-index: 5; }}
      #cena-logo {{ z-index: 6; }}
      #lente-a {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }}
      #lente-a video {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="28.4" data-width="1080" data-height="1920">
      <div id="fundo-host" class="clip" data-composition-id="fundo" data-composition-src="compositions/fundo.html" data-start="0" data-duration="28.4" data-track-index="0" data-track-kind="graphics"></div>

      <!-- gancho: a peça pronta em tela cheia -->
      <div id="cena-gancho" class="cena">
        <div id="lente-a" data-layout-allow-overflow>
          <video id="v-gancho" class="clip" src="assets/montagem.mp4" data-start="0" data-duration="2.8" data-media-start="30.8" data-playback-rate="0.6" data-track-index="1" muted playsinline></video>
        </div>
{host("abertura", 0, 2.8, 2)}      </div>

      <!-- os seis passos da montagem, em cartões que correm para a esquerda -->
{cenas}
      <!-- a peça pronta sobe -->
      <div id="cena-peca" class="cena">
{host("peca", 19.6, 4, 4)}      </div>

      <div id="hud-host" class="clip" data-composition-id="hud" data-composition-src="compositions/hud.html" data-start="2.8" data-duration="16.8" data-track-index="5" data-track-kind="graphics"></div>

      <!-- chegada do logo -->
      <div id="cena-logo" class="cena">
{host("logo", 23.6, 4.8, 6)}      </div>

{auds}    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});

      // gancho: a câmera chega na peça pronta e assenta
      tl.fromTo("#lente-a", {{ scale: 1.37, x: 128, y: 322, transformOrigin: "50% 50%" }}, {{ scale: 1.32, x: 130, y: 300, duration: 1.1, ease: "expo.out" }}, 0);

      // <seams:auto>
      // </seams:auto>

      tl.set({{}}, {{}}, 28.4);
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""
open(f"{P}/index.html", "w").write(INDEX)

# ---------------------------------------------------------------- ledger
cuts = [("gancho→passo 1", 2.8, "#cena-gancho", "#cena-1")]
for k in range(1, 6):
    cuts.append((f"passo {k}→passo {k+1}", PASSOS[k][1], f"#cena-{k}", f"#cena-{k+1}"))
seams = [{"id": i, "cut": c, "technique": "cut-the-curve LEFT",
          "exit": {"selector": a, "axis": "x", "dir": -1},
          "entry": {"selector": b, "axis": "x", "dir": -1, "travel": 14}} for i, c, a, b in cuts]
seams.append({"id": "passo 6→peça pronta", "cut": 19.6, "technique": "cut-the-curve UP (elevação: a conclusão sobe)",
              "exit": {"selector": "#cena-6", "axis": "y", "dir": -1},
              "entry": {"selector": "#cena-peca", "axis": "y", "dir": -1, "travel": 14}})
seams.append({"id": "peça pronta→logo", "cut": 23.6, "technique": "inverse zoom (chegada da marca)",
              "exit": {"selector": "#cena-peca", "axis": "z", "dir": -1},
              "entry": {"selector": "#cena-logo", "axis": "z", "dir": -1, "scanRoot": "#cena-logo"}})
json.dump({"fps": 30, "seams": seams}, open(f"{P}/ledger.json", "w"), indent=2, ensure_ascii=False)
json.dump({"id": "video-cassi-print-motion", "name": "video-cassi-print-motion", "createdAt": "2026-11-11T01:00:00.000Z"},
          open(f"{P}/meta.json", "w"), indent=2)
print("ok")
