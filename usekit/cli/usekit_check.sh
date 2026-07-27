#!/data/data/com.termux/files/usr/bin/bash
# usekit_check.sh — 1층 기계 검증 (job 보고와 무관하게 디스크 직접 판정)
#
# 사용: 지시서 끝 "## CHECK" 블록을 이 스크립트에 먹인다.
#   bash usekit_check.sh CHECK_block.txt        (또는 stdin)
#
# CHECK 문법 (한 줄=한 검사, #주석/빈줄 무시):
#   root: <PROJECT 절대경로>        이후 파일은 이 기준 상대경로
#   node: <file.js>                 node --check 문법
#   grep0: <file> <pattern>         매치 0줄이어야 PASS (있으면 안 되는 것)
#   grepc: <file> <pattern> <N>     매치 줄수 == N
#   grepge: <file> <pattern> <N>    매치 줄수 >= N
#   divbalance: <file.html>         '<div' 수 == '</div>' 수
# 종료코드: 전부 PASS면 0, FAIL 있으면 1.

ROOT="/storage/emulated/0/DEV/PROJECT/usekit/tools/editor"
PASS=0; FAIL=0
GREEN=$'\033[32m'; RED=$'\033[31m'; DIM=$'\033[2m'; RST=$'\033[0m'

abspath() { case "$1" in /*) printf '%s' "$1";; *) printf '%s/%s' "$ROOT" "$1";; esac; }
count() { grep -E -- "$2" "$1" 2>/dev/null | wc -l | tr -d ' '; }
report() {
  if [ "$1" -eq 0 ]; then PASS=$((PASS+1)); printf "  ${GREEN}PASS${RST}  %-11s %s\n" "$2" "$3"
  else FAIL=$((FAIL+1)); printf "  ${RED}FAIL${RST}  %-11s %s\n" "$2" "$3"; fi
}

SRC="${1:-/dev/stdin}"
echo "── usekit_check ──"
while IFS= read -r line || [ -n "$line" ]; do
  line="${line%$'\r'}"
  case "$line" in ''|\#*) continue;; esac
  cmd="${line%%:*}"; rest="${line#*:}"; rest="${rest#"${rest%%[![:space:]]*}"}"
  case "$cmd" in
    root) ROOT="$rest"; echo "${DIM}root = $ROOT${RST}";;
    node)
      f="$(abspath "$rest")"
      if [ ! -f "$f" ]; then report 1 "node" "$rest (파일없음)"
      elif node --check "$f" 2>/dev/null; then report 0 "node" "$rest"
      else report 1 "node" "$rest (문법오류)"; fi;;
    grep0)
      set -- $rest; file="$1"; shift; pat="$*"
      n=$(count "$(abspath "$file")" "$pat")
      if [ "$n" -eq 0 ]; then report 0 "grep0" "$file  /$pat/ = 0"
      else report 1 "grep0" "$file  /$pat/ = $n (0이어야)"; fi;;
    grepc)
      set -- $rest; file="$1"; exp="${@: -1}"
      pat="${rest#"$file"}"; pat="${pat%"$exp"}"; pat="$(printf '%s' "$pat" | sed 's/^ *//;s/ *$//')"
      n=$(count "$(abspath "$file")" "$pat")
      if [ "$n" -eq "$exp" ]; then report 0 "grepc" "$file  /$pat/ = $n (==$exp)"
      else report 1 "grepc" "$file  /$pat/ = $n (기대 $exp)"; fi;;
    grepge)
      set -- $rest; file="$1"; exp="${@: -1}"
      pat="${rest#"$file"}"; pat="${pat%"$exp"}"; pat="$(printf '%s' "$pat" | sed 's/^ *//;s/ *$//')"
      n=$(count "$(abspath "$file")" "$pat")
      if [ "$n" -ge "$exp" ]; then report 0 "grepge" "$file  /$pat/ = $n (>=$exp)"
      else report 1 "grepge" "$file  /$pat/ = $n (기대 >=$exp)"; fi;;
    divbalance)
      f="$(abspath "$rest")"
      o=$(grep -o '<div' "$f" 2>/dev/null | wc -l | tr -d ' ')
      c=$(grep -o '</div>' "$f" 2>/dev/null | wc -l | tr -d ' ')
      if [ "$o" -eq "$c" ]; then report 0 "divbalance" "$rest  <div>=$o </div>=$c"
      else report 1 "divbalance" "$rest  <div>=$o </div>=$c (불균형)"; fi;;
    *) report 1 "?" "알 수 없는 검사: $line";;
  esac
done < "$SRC"
echo "──────────────────"
printf "총 %d  ${GREEN}PASS %d${RST}  ${RED}FAIL %d${RST}\n" "$((PASS+FAIL))" "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
