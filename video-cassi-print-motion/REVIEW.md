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

## Revisão com a skill motion-design (LottieFiles)

Personalidade escolhida: brincalhona/energética (combina com o logo e a peça). Ajustes aplicados:
- **Follow-through e arco nos cartões:** entram inclinados 3° ("arrastados") e assentam com `back.out(1.4)`; na saída
  inclinam −2.5° na direção do movimento; a sombra cresce 80 ms depois do cartão (camada secundária).
- **Squash e causa na peça pronta:** sobe, passa do ponto (−28 px), cai e achata 2 quadros (1.06 × 0.93) ao pousar,
  recupera com overshoot; a sombra acompanha. O pouso dispara o confete (agora saindo por trás da peça), o texto
  e o impacto grave — o riser culmina no pouso (T 20.04 s).
- **Parallax corrigido:** as faixas do fundo andavam mais que os cartões; agora andam 160/100 px por corte
  (~25–30% do primeiro plano), como camada distante.
- **Ação secundária na chamada:** um brilho atravessa a pílula uma vez, 50 ms depois de ela pousar.
- Não aplicado: "pulso/respiração" ambiente em loop — o motion-doctrine do projeto proíbe movimento ocioso; a
  camada ambiente é o fundo que anda nos cortes.

Check ok; Seam Gate 8/8 PASS (na cópia sem vídeo); áudio −13.9 LUFS, pico −1.0 dBTP.
