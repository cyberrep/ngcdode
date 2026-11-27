#!/bin/bash
# Monta os patches do BIOS do Neo CD SD Loader (3 alvos) e gera os 4 SPATxxxx.p
# uso: build_patch.sh PASTA_FONTE PASTA_SAIDA
#
# Compatibilidade com o ASW antigo do furrtek (validado byte a byte contra o NSDL0011.WAD oficial):
#  - caminhos com '\' nos INCLUDE/BINCLUDE viram '/'
#  - 'movea.l aN,memoria' (o ASW antigo aceitava) vira 'move.l'
#  - PADDING: o ASW antigo completava todo dc.b/ds.b impar -> ALIGN 2 (fix_ram_padding.py)
#  - \{NUM} nos textos sai em decimal -> OUTRADIX 10
set -e
SRC=$(realpath "$1"); OUT=$(realpath -m "$2")
TOOLS=$(dirname "$(realpath "$0")")/../tools; BIN=$TOOLS/bin
mkdir -p "$OUT"; TMP=$(mktemp -d); cp -r "$SRC"/. "$TMP"/; cd "$TMP"

sed -i -E '/^\s*B?INCLUDE/I s#\\#/#g' *.asm
sed -i -E 's/movea\.l(\s+a[0-7]),(\s*[A-Za-z_])/move.l\1,\2/' *.asm
python3 "$TOOLS/fix_ram_padding.py" *.asm
python3 - <<'EOF'
import re
t = open('main.asm', encoding='latin-1').read()
t = re.sub(r'(?im)^(\s*supmode\s+on.*)$', r'\1\n    OUTRADIX 10', t, count=1)
open('main.asm', 'w', encoding='latin-1').write(t)
EOF

build() {
  "$BIN/asl" -cpu 68000 -q -L -D TARGET=$1 main.asm -o main.p > asl_$1.log 2>&1 || { cat asl_$1.log; exit 1; }
  grep -iE "error" asl_$1.log | head -5 || true
}
build 1; cp main.p "$OUT/SPAT64DC.p"; cp main.lst "$OUT/main-front.lst"
build 2; cp main.p "$OUT/SPATE10C.p"; cp main.p "$OUT/SPATDC4C.p"; cp main.lst "$OUT/main1-2.lst"
build 3; cp main.p "$OUT/SPATEF2E.p"; cp main.lst "$OUT/main3.lst"
rm -rf "$TMP"; echo "patches em $OUT"
