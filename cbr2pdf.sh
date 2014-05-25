#!/bin/bash
#
# Convert Comic Book Archives (CBRs) to PDFs, mostly for printing
#
# Dependencies: unrar, findutils, ImageMagick
set -o errexit

IN=${1?"Usage: $0 [INPUT]"}
OUT="${1%.*}.pdf"

TEMPIN=$(mktemp --tmpdir --directory cbr2pdf.XXXXXXX)
trap 'rm -rf "$TEMPIN"' EXIT
unrar x -c- -idq "$IN" "$TEMPIN"

{ find "$TEMPIN" -type f -print0 | sort -z ; echo -n "$OUT"; } \
    | xargs -0 -x convert -rotate "90>" -page A4
