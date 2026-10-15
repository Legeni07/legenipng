#!/usr/bin/env bash
# Recette de l'API LegeniPNG.
# Usage : bash tests/test_api.sh <photo.jpg> [<fond.jpg>] [URL]   (URL par défaut : http://127.0.0.1:9650)
set -u
IMG=${1:?photo de test attendue}
BGIMG=${2:-$IMG}
BASE=${3:-http://127.0.0.1:9650}
OUT=${OUT:-/tmp/legenipng_test}
HERE=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$OUT"
PASS=0; FAIL=0

check() { # nom, code attendu, puis arguments curl
  local name=$1 expected=$2; shift 2
  [ "${1:0:1}" = "-" ] && set -- "$@" "$P"  # options seules : appel de /api/process
  local hdr="$OUT/$name.headers" body="$OUT/$name.out"
  local code t
  read -r code t < <(curl -s -o "$body" -D "$hdr" -w '%{http_code} %{time_total}\n' "$@")
  if [ "$code" = "$expected" ]; then
    PASS=$((PASS+1)); printf 'OK    %-24s %s  %6.2fs' "$name" "$code" "$t"
  else
    FAIL=$((FAIL+1)); printf 'ECHEC %-24s %s (attendu %s)' "$name" "$code" "$expected"
  fi
  if [ "$code" = 200 ] && grep -qi '^x-legenipng-report' "$hdr"; then
    grep -i '^x-legenipng-report' "$hdr" | sed 's/^[^:]*: //' | python3 "$HERE/report_summary.py"
    mv "$body" "$OUT/$name.$(grep -i '^content-type' "$hdr" | sed 's#.*image/##; s/\r//; s/jpeg/jpg/')"
  elif [ "$code" != 200 ]; then
    printf '  -> %s' "$(head -c 160 "$body")"
  fi
  echo
}

P="$BASE/api/process"
check health 200 "$BASE/api/health"
check config 200 "$BASE/api/config"
check page 200 "$BASE/"

# Détourage, chaque modèle
for m in isnet-general-use u2net u2net_human_seg u2netp; do
  check "cut_$m" 200 -F "image=@$IMG" -F remove_bg=true -F model=$m
done
check cut_standard 200 -F "image=@$IMG" -F remove_bg=true -F edges=standard
check cut_matting  200 -F "image=@$IMG" -F remove_bg=true -F edges=matting
check bg_color     200 -F "image=@$IMG" -F remove_bg=true -F bg_mode=color -F bg_color=#1f3a8a -F output_format=jpg
check bg_blur      200 -F "image=@$IMG" -F remove_bg=true -F bg_mode=blur -F bg_blur=70 -F output_format=jpg
check bg_image     200 -F "image=@$IMG" -F remove_bg=true -F bg_mode=image -F "background_image=@$BGIMG" -F output_format=webp

# Correction
check enhance_auto   200 -F "image=@$IMG" -F enhance_mode=auto -F output_format=jpg
check enhance_manual 200 -F "image=@$IMG" -F enhance_mode=manual -F wb=60 -F levels=50 -F exposure=40 \
  -F local_contrast=30 -F denoise=30 -F sharpen=40 -F vibrance=30 -F output_format=jpg

# Agrandissement IA
check up_x2_low  200 -F "image=@$IMG" -F upscale=2 -F sr_denoise=low -F output_format=jpg
check up_x4_med  200 -F "image=@$IMG" -F upscale=4 -F sr_denoise=medium -F output_format=jpg
check all_in_one 200 -F "image=@$IMG" -F enhance_mode=auto -F remove_bg=true -F upscale=2 -F output_format=webp

# Erreurs attendues
head -c 2048 /dev/urandom > "$OUT/bruit.bin"
check err_not_image   415 -F "image=@$OUT/bruit.bin"
check err_bad_model   400 -F "image=@$IMG" -F remove_bg=true -F model=inexistant
check err_bad_value   400 -F "image=@$IMG" -F enhance_mode=manual -F wb=150
check err_bad_color   400 -F "image=@$IMG" -F remove_bg=true -F bg_mode=color -F bg_color=rouge
check err_bad_upscale 400 -F "image=@$IMG" -F upscale=3
check err_missing_bg  400 -F "image=@$IMG" -F remove_bg=true -F bg_mode=image
head -c $((16*1024*1024)) /dev/zero > "$OUT/gros.bin"
check err_too_large   413 -F "image=@$OUT/gros.bin"

# Aucune métadonnée dans les résultats
if python3 - "$OUT" <<'PY'
import sys, glob
bad = [f for f in glob.glob(sys.argv[1] + "/*.jpg") if b"Exif" in open(f, "rb").read()[:4096]]
sys.exit(1 if bad else 0)
PY
then PASS=$((PASS+1)); echo "OK    sans EXIF dans les JPEG produits"
else FAIL=$((FAIL+1)); echo "ECHEC EXIF présent dans un résultat"; fi

echo "----"
echo "$PASS réussis, $FAIL échecs. Fichiers : $OUT"
[ "$FAIL" = 0 ]
