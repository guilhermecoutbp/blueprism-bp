# Revisão: "O traço"

Render: `renders/vellaro-o-traco.mp4`, 1080 x 1920, 30 fps, 28,0 s, H.264 + AAC 48 kHz, -15,9 LUFS integrado.

## Quadros revistos (snapshot)

| Tempo | O que se vê | Situação |
|---|---|---|
| 0 s | papel, régua apoiada e lápis no início da primeira parede | ok: não é preto vazio nem o logo |
| 0,8–7,5 s | paredes uma a uma, régua girando entre elas, câmera de 1,1x a 0,94x | ok; a régua centrada no traço nunca desce sobre a frase |
| 9–12,5 s | cotas 6,40 / 6,70 / 2,00 / 0,82 contando, legíveis | ok |
| 14–18,2 s | bancada, ilha e painel ripado; fitas de latão acesas | ok |
| 19,6–20,4 s | última linha em latão; a planta recua | ok |
| 22,4 s | só a linha de latão no papel (pausa) | ok |
| 23,3–25,3 s | a linha se abre até 680 px; VELLARO traçado e preenchido; DESIGN por desfoque | ok |
| 27,75 s | logo completo, centrado, @vellaro_design, dentro da faixa segura | ok |

## Som (medido, não ouvido)

- voz 1: 0,52–2,36 s · voz 2: 8,52–11,14 s · voz 3: 13,52–15,56 s · voz 4 "Vellaro Design.": 24,62–25,66 s
- cliques suaves no fim de cada cota (9,4 / 11,0 / 11,6 / 12,2 s), sopro na última linha (19,3 s)
- sem música no arquivo: a trilha entra pela biblioteca do Instagram

## Avisos do check que ficaram

- `dead_stretch` 2,25–5,88 s: falso positivo; o desenho é SVG movido pelo relógio e segue sendo traçado nesse trecho (visto nos quadros 2,5 / 3,5 / 4,5 / 5,5 s).
- `composition_file_too_large` (desenho.html, 444 linhas): a cena é um único sistema de desenho; dividir pioraria a leitura.
- `clip_media_fit` voz 1: diferença de 0,05 s entre o arquivo e o slot, sem efeito.
