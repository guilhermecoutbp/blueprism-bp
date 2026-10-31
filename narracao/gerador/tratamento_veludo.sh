#!/bin/bash
# Aplica o tratamento "veludo" a um WAV cru: $1 entrada, $2 saída, $3 = "tom" para baixar o tom levemente
in=$1; out=$2
pitch=""; [ "$3" = "tom" ] && pitch="rubberband=pitch=0.9604:formant=preserved:pitchq=quality,"
ffmpeg -y -loglevel error -i "$in" -af "aresample=44100:resampler=soxr,highpass=f=75,${pitch}lowshelf=f=220:g=2.5,equalizer=f=2900:t=q:w=1.1:g=-3,highshelf=f=8000:g=-3,deesser=i=0.45,acompressor=threshold=-24dB:ratio=2.2:attack=25:release=220:makeup=2:knee=6,aecho=0.85:0.6:16|29:0.07|0.045,loudnorm=I=-18:TP=-1.5:LRA=6,afade=t=in:d=0.04" -ac 1 -ar 44100 -b:a 80k "$out"
