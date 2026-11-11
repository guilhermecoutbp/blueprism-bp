#!/bin/bash
# Regenera o projeto: gera as cenas → carimba as transições do ledger → aplica o grade nos vídeos.
# Uso (na pasta do projeto): ./tools/build.sh
set -e
cd "$(dirname "$0")/.."
python3 -I tools/gerar.py .
node ../.claude/skills/motion-doctrine/scripts/seam-stamp.mjs --ledger ledger.json --write index.html
G='{"intensity":0.7,"adjust":{"exposure":0.01,"contrast":0.07,"highlights":-0.06,"shadows":0.04,"vibrance":0.06,"saturation":0.04}}'
ap(){ npx hyperframes media-treatment --file "$1" --selector "$2" --grading "$G" --apply --json >/dev/null 2>&1 && echo "grade $2"; }
ap index.html "#v-gancho"
ap compositions/passo-1.html "#v-pecas"; ap compositions/passo-2.html "#v-rosto"; ap compositions/passo-3.html "#v-chapeu"
ap compositions/passo-4.html "#v-dentes"; ap compositions/passo-5.html "#v-bracos"
ap compositions/passo-6.html "#v-base"; ap compositions/passo-6.html "#v-barco"; ap compositions/peca.html "#peca-img"
