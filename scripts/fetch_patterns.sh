#!/bin/sh
# Golly 同梱の JvN29 パターンを patterns/ に取得する (Golly は GPL-2)
set -e
cd "$(dirname "$0")/../patterns"
BASE=https://raw.githubusercontent.com/AlephAlpha/golly/master/Patterns/Self-Rep/JvN
for f in small-JvN-self-replicator.rle cell-coders-demo.rle counter-demo.rle read-arm-demo.rle; do
  [ -f "$f" ] || { echo "取得: $f"; curl -sfL "$BASE/$f" -o "$f"; }
done
ls -l *.rle
