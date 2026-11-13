# Rota até Teresópolis — Seu negócio no mapa

Animação cinematográfica de 20 s (1920×1080) em um único arquivo HTML com Three.js:
a viagem de carro da Tv. Teodomiro Pereira, 300 (Freguesia, Jacarepaguá) até a
casa Airbnb da Rua Brasília, 333, em Teresópolis.

## Como ver

Abra `index.html` em um navegador com WebGL 2 e clique em reproduzir (o som só
começa depois do clique, por regra dos navegadores). Espaço pausa; a barra
inferior tem posição, reinício e som.

## O que tem dentro

- **Rota real, passo a passo**: os 23 passos do roteiro, com os nomes das vias e
  as distâncias informadas (≈ 101 km). As rodovias seguem coordenadas
  geográficas aproximadas; as ruas de saída e de chegada são traçadas a partir
  das distâncias e curvas do roteiro, sem atalhos.
- **Mapa 3D branco**: relevo procedural moldado pela geografia da região
  (Maciço da Tijuca, Baía de Guanabara, Baixada Fluminense, Serra dos Órgãos),
  cerca de 48 mil construções fundidas em malhas por bloco, vias, vegetação e névoa por distância.
- **Câmera contínua**: uma única trajetória orbital, sem cortes, do logotipo até
  a fachada da casa e a visão da rota completa.
- **Motion blur por acumulação**: 16 subquadros por quadro, com obturador de
  180°. Em máquinas lentas o número de subquadros cai sozinho (indicado na barra).
- **Pedágios**: Linha Amarela e BR-116, com trecho âmbar na rota, pórtico 3D e aviso.
- **Trilha**: sintetizada em Web Audio a 120 BPM, com whooshes nas transições. Ao carregar,
  a página renderiza a trilha num `OfflineAudioContext` e a toca por um `<audio>` (assim ela
  soa mesmo com o iPhone no silencioso); se isso falhar, toca no `AudioContext` ao vivo.

## Renderizar em vídeo

`index.html#capture` esconde os controles e deixa o palco em 1920×1080. A página
expõe `window.__film`:

- `__film.seek(t, 16)` desenha o quadro do instante `t` (em segundos) com 16 subquadros;
- `await __film.audioWav()` devolve a trilha em WAV (base64), renderizada offline.

Capture os quadros com Playwright ou Puppeteer em uma máquina com GPU e junte
com o áudio no ffmpeg.
