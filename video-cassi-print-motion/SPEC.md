# Cassi Print — versão motion graphic (vertical)

FORMAT: 1080×1920, 30 fps, 28.4 s. Mesma gravação, trilha (150 bpm, cortes em múltiplos de 0.4 s) e paleta da v1
(marinho #1a2530, laranja #e78d33, azul #45839a, creme #f7f3ec; Nunito 900).

CORRENTE: tudo anda para a ESQUERDA (cartões, faixas do fundo, painel). Vetores reservados: PARA CIMA na conclusão
(a peça pronta sobe), ZOOM PARA TRÁS na chegada da marca. Ledger em `ledger.json`; transições carimbadas com
`seam-stamp.mjs` e verificadas com `seam-gate.mjs` (8/8 PASS).

| T | Cena | O que se move (rota de movimento contínuo) |
|---|---|---|
| 0.0–2.8 | Gancho: peça pronta em tela cheia, "IMPRESSO EM 3D" | câmera assenta; selo "Feito à mão" carimbado (0.8 s); golpe no título (1.6 s) |
| 2.8–19.6 | 6 passos em cartões com borda laranja | painel da impressora: PASSO 01→06, nome rola, barra e % sobem passo a passo; legendas batem palavra a palavra com tarja; punch-ins na batida; círculo desenhado nos dentes (passo 4) |
| 19.2–19.6 | pausa antes do clímax | painel em 100% "Pronto!" |
| 19.6–23.6 | Peça pronta sobe (recorte) | raios explodem e desaceleram; confete; "FEITO EM 3D. MONTADO À MÃO." |
| 23.6–28.4 | Logo chega (zoom para trás) | camadas laranja "terminam de imprimir"; chamada "Encomende já a sua" |

Editar: os textos e tempos estão em `tools/gerar.py`; rode `./tools/build.sh` para regenerar (o build reaplica o grade).
