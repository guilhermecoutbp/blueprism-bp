# Revisão — versão motion graphic (28.4 s)

- **Check:** ok (sem erros). Aviso aceito: `v-barco` com data-start local 1.6 dentro da cena do passo 6 (intencional).
- **Seam Gate:** 8/8 transições PASS — direção, corte em movimento dos dois lados, velocidades casadas (razão 1.14),
  sem sobreposição, sinal do zoom coerente. Medido numa cópia sem os `<video>`: o seek do gate não espera os
  vídeos carregarem e lê tudo parado; as transições estão nos wrappers, então a medição vale para o projeto real.
  Os snapshots do render confirmam.
- **Quadros conferidos:** capa (0 s) com título legível sobre a estante; círculo dos dentes na posição dos dentes
  a partir de 0.8 s do plano; painel sai para cima no corte da peça pronta (chapéu visível); faixas do fundo não
  encostam na frase final.
- **Som (medido, não ouvido):** −13.9 LUFS, pico −1.1 dBTP, sem clipping. Whooshes em 3 versões alternadas nos
  cortes, clique no círculo, riser → impacto na peça pronta, impacto grave na chegada do logo, pop no selo e na chamada.
- Limites: fonte 720p (cartões ampliam 1.25×); nos primeiros 0.3 s do passo 4 a câmera ainda está se mexendo.
