// Narração sincronizada com a rolagem.
// Cada etapa do site tem uma fala; ela começa quando o texto da etapa aparece.
// Se outra etapa entra antes da fala terminar, a atual some suavemente e a nova começa.
// O áudio só é baixado depois que a pessoa ativa o som (os navegadores exigem um toque).

const FILES = ["01-entrada", "02-papel", "03-medida", "04-volume", "05-acabamento", "06-final"];
const FADE_OUT = 0.45;
const FADE_IN = 0.12;

export function createNarrator({ base = "audio/", onChange = () => {} } = {}) {
  let ctx = null;
  let master = null;
  let buffers = null;
  let enabled = false;
  let active = -1; // etapa visível agora (-1 entre etapas)
  let lastPlayed = -1; // última etapa narrada
  let current = null; // fala tocando agora

  function load() {
    if (buffers) return;
    // Baixa todas em paralelo; cada fala pode tocar assim que a sua chegar
    buffers = FILES.map((name) =>
      fetch(`${base}${name}.mp3`)
        .then((r) => r.arrayBuffer())
        .then((data) => ctx.decodeAudioData(data))
        .catch(() => null),
    );
  }

  function stopCurrent(fade = FADE_OUT) {
    if (!current) return;
    const { src, gain } = current;
    const t = ctx.currentTime;
    gain.gain.cancelScheduledValues(t);
    gain.gain.setValueAtTime(gain.gain.value, t);
    gain.gain.linearRampToValueAtTime(0, t + fade);
    try {
      src.stop(t + fade + 0.05);
    } catch {
      /* já parou */
    }
    current = null;
  }

  async function play(index) {
    const buffer = await buffers[index];
    // A pessoa pode ter rolado para outra etapa enquanto o áudio carregava
    if (!enabled || !buffer || index !== active) return;
    const overlap = current ? 0.28 : 0;
    stopCurrent();
    const src = ctx.createBufferSource();
    src.buffer = buffer;
    const gain = ctx.createGain();
    const start = ctx.currentTime + overlap;
    gain.gain.setValueAtTime(0, start);
    gain.gain.linearRampToValueAtTime(1, start + FADE_IN);
    src.connect(gain).connect(master);
    src.start(start);
    const playing = { src, gain, index };
    current = playing;
    lastPlayed = index;
    onChange({ enabled, speaking: true });
    src.onended = () => {
      if (current === playing) {
        current = null;
        onChange({ enabled, speaking: false });
      }
    };
  }

  // Chamado a cada quadro com a etapa visível: 0 = entrada, 1..5 = etapas, -1 = entre etapas
  function update(index) {
    if (index === active) return;
    active = index;
    if (!enabled || index < 0) return; // entre etapas, deixa a fala atual terminar
    if (index === lastPlayed) return; // não repete a mesma etapa ao oscilar na borda
    play(index);
  }

  async function enable() {
    if (!ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return false;
      ctx = new AC();
      master = ctx.createGain();
      master.gain.value = 1;
      master.connect(ctx.destination);
    }
    await ctx.resume();
    enabled = true;
    load();
    lastPlayed = -1;
    onChange({ enabled, speaking: false });
    if (active >= 0) play(active);
    return true;
  }

  function disable() {
    enabled = false;
    if (ctx) {
      stopCurrent(0.3);
      setTimeout(() => !enabled && ctx.suspend(), 400);
    }
    onChange({ enabled, speaking: false });
  }

  document.addEventListener("visibilitychange", () => {
    if (!ctx) return;
    if (document.hidden) ctx.suspend();
    else if (enabled) ctx.resume();
  });

  return {
    update,
    enable,
    disable,
    toggle: () => (enabled ? disable() : enable()),
    get enabled() {
      return enabled;
    },
  };
}
