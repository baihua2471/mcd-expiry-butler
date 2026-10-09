#!/usr/bin/env bash
# 把本仓库安装为 WorkBuddy 可识别的 Skill。
#
# 用法：
#   bash scripts/install_skill.sh              # 安装到用户级 ~/.workbuddy/skills/
#   bash scripts/install_skill.sh --project    # 安装到当前项目 .workbuddy/skills/
#
# 重新执行即可覆盖更新（源码只有仓库里这一份，安装目录是副本）。
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${1:-}" == "--project" ]]; then
  DST="$(pwd)/.workbuddy/skills/mcd-expiry-butler"
else
  DST="$HOME/.workbuddy/skills/mcd-expiry-butler"
fi

mkdir -p "$DST"
rm -rf "$DST/src" "$DST/scripts" "$DST/SKILL.md"

cp "$SRC/skill/mcd-expiry-butler/SKILL.md" "$DST/SKILL.md"
cp -R "$SRC/src" "$DST/src"
cp -R "$SRC/scripts" "$DST/scripts"

echo "[ok] Skill 已安装到：$DST"
echo "[ok] 目录内容："
ls -1 "$DST"
echo
echo "验证："
echo "  cd '$DST' && PYTHONPATH=src python3 -m expiry_butler.cli --case src/fixtures/demo_case.json --out /tmp/mcd_demo.html"
