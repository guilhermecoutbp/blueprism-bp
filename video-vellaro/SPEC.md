# Vellaro Design: "O traço"

GOAL:    quem assiste sente o cuidado de um projeto sob medida, do primeiro traço à assinatura, e guarda o nome Vellaro Design.
OUTPUT:  HyperFrames, 1080 x 1920 (9:16, Reels), 30 fps.
TIME:    28 s x 30 fps = 840 quadros. Sem música no arquivo (a trilha entra pela biblioteca do Instagram); a narração é o relógio.

## LOOK

O meio é **desenho técnico em papel preto de algodão, com grafite prateado**:

- **Papel** (fundo): `#121110`, com fibra de algodão em ruído fixo a 3,5% de opacidade e uma grade técnica de 24 px a 3,5% de opacidade, que some nas bordas. Vinheta de 18% nos cantos. Nunca um vazio: o papel tem textura e a planta ocupa 72% da largura.
- **Grafite** (tinta): `#cfcbc4`. Paredes com dupla linha de 2,2 px e 18 px entre elas, preenchidas por hachura a 45° (linhas de 1 px a cada 7 px, 35%). Linhas de construção de 1 px a 18%, que passam 22 px das pontas, como à mão. Cotas de 1,2 px a 70%.
- **Latão** (único destaque): `#c9a36a`. Só pode aparecer na ponteira do lápis, nas fitas de luz sob os móveis, na linha final e no traço do logo. Nunca em texto de leitura.
- **Tipos**: frases em EB Garamond 400, 60 px (3,1% da altura), entrelinha 1,15, tracking 0. Números das cotas em Montserrat 400, 26 px, tracking +2%. Logo: o vetor oficial do VELLARO, com 680 px de largura (63% do quadro).
- **Objetos**: a régua de aço escovado (60 x 940 px) e a lapiseira de desenho (ver OBJECTS).
- **Luz e profundidade**: luz da esquerda alta. Sombra das ferramentas a 18 px à direita e 24 px abaixo, desfoque de 14 px, 45% de opacidade. Quando o lápis é levantado, a sombra se afasta para 30/40 px e desfoca 20 px.

## OBJECTS

- **Lapiseira de desenho**: corpo de metal grafite `#2a2a2c` com reflexo vertical (gradiente de 4 paradas), empunhadura serrilhada (linhas de 1 px a cada 4 px), anel e ponteira cônica em latão, e o grafite exposto em `#9a9893`. Mede 30 x 470 px e fica inclinada a -32°, com a ponta exatamente no ponto que está sendo desenhado.
- **Régua de aço**: barra de aço escovado (gradiente `#8f9196` → `#d9dadd` → `#a7a9ad`, com riscos horizontais de 1 px a 6%), marcações de milímetro em `#2b2b2b` (cm com 18 px de altura, meio cm 12 px, mm 7 px) e números de 0 a 30 em Montserrat 14 px. Tem um bisel claro de 1 px na borda de desenho.
- **Planta**: um ambiente de 6,40 x 6,70 m: paredes externas, uma parede interna com passagem, uma porta com o arco de abertura (raio de 100 px) e uma janela com três linhas finas.
- **Marcenaria** (dentro da planta): bancada de cozinha encostada na parede de cima, ilha central e painel ripado na parede esquerda. Contorno em grafite, hachura de 1 px e, embaixo de cada peça, uma fita de luz em latão de 3 px com halo de 6 px a 35%.

## MOTION

- **Eases**: chegada `expo.out`, deslocamento de ferramentas e câmera `power2.inOut`, saída `power3.in`. O traço avança a velocidade constante, com 6 quadros de aceleração no início e 6 de frenagem no fim de cada linha.
- **Velocidade do traço**: 900 px/s com a régua e 650 px/s à mão livre. Entre uma linha e outra, o lápis levanta em 6 quadros, viaja em 12 a 18 quadros e baixa em 5.
- **Régua**: gira e desliza até a próxima parede em 15 quadros (`power2.inOut`) e só depois o lápis desce.
- **Frases**: entram palavra a palavra, cada uma com desfoque de 6 → 0 px e opacidade 0 → 1 em 4 quadros, 2 quadros entre palavras, sem deslocamento, sincronizadas com a voz. Saem com desfoque de 8 px em 6 quadros. Paradas enquanto são lidas.
- **Números das cotas**: contam de 0,00 até o valor em 18 quadros (`power3.out`).
- **Logo**: cada letra é traçada (linha de 1,2 px) em 14 quadros, 3 quadros entre letras, depois preenchida em 10 quadros. DESIGN entra por desfoque.

## SHOTS

(Tempos finais ajustados à duração real de cada fala.)

| Quadros | O movimento principal | O que se lê | Som | Passagem |
|---|---|---|---|---|
| 0–90 | A régua já está apoiada; o lápis traça a primeira parede (câmera a 1,55x sobre o canto superior esquerdo) | "Todo projeto começa com um traço." (a partir do quadro 12) | voz 1 | o traço termina e a régua gira para a próxima parede |
| 90–240 | Paredes uma a uma; a câmera se afasta até 1,0x (`power2.inOut`, 150 quadros); depois porta, arco e janela à mão livre | — | — | a última janela termina e o lápis vai até a primeira cota |
| 240–390 | As cotas entram uma a uma e os números contam | "Cada medida, pensada para o seu espaço." | voz 2; clique suave a cada cota (3 tomadas alternadas) | o lápis sai da cota e entra no ambiente |
| 390–570 | A marcenaria é desenhada dentro da planta; as fitas de latão acendem uma a uma | "Até o desenho se tornar o seu lugar." | voz 3 | a régua sai de cena pela direita |
| 570–660 | O lápis faz a última linha: sai da planta e cruza até o centro, virando uma linha horizontal de latão; a planta escurece até 20% e a câmera centraliza a linha | — | whoosh baixo | o lápis sai pela direita e a linha fica |
| 660–690 | Pausa: só a linha de latão sobre o papel | — | silêncio | — |
| 690–840 | VELLARO é traçado letra por letra acima da linha, preenche, e DESIGN surge abaixo; @vellaro_design por último | "VELLARO / DESIGN", "@vellaro_design" | voz 4: "Vellaro Design." | fim parado por 1,5 s |

## BANNED

Os padrões de vídeo gerado (`spec.md`) e, especificamente neste filme:

- uma mão desenhada ou fotos de mão;
- brilho, bloom, partículas, lens flare; o latão nunca vira neon;
- legendas em caixa ou "pílulas"; rótulos em monoespaçada; numeração "01 / 02";
- frases deslizando para cima ao entrar; texto se mexendo enquanto é lido;
- a planta inteira aparecendo de uma vez; a régua flutuando sem tocar o papel;
- logo no canto; logo que só aparece com fade.

## QA

- q0 (frame 0): o papel, a régua e o lápis no meio da primeira linha. Não pode ser preto vazio nem o logo.
- q120: a planta está nascendo, com as ferramentas encostadas no papel e a sombra na direção certa.
- q300: todas as cotas visíveis e legíveis a 360 px de largura.
- q520: marcenaria e fitas de latão acesas, frase 3 inteira.
- q650: só a linha de latão no centro.
- q800: logo completo, centralizado e dentro da faixa segura (y entre 168 e 1330 px).
