#!/usr/bin/env python3
"""演示模式：用样例数据生成结果页。

输出顶部会明确标注“样例数据，非实时账户结果”，不会去查任何真实账号。
用法：
    python scripts/run_demo.py
    python scripts/run_demo.py --out demo_output/demo_report.html
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from expiry_butler import build_report, load_case, render_html  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="麦麦权益到期管家 · 演示模式")
    parser.add_argument(
        "--case",
        default=str(ROOT / "src/fixtures/demo_case.json"),
        help="样例数据路径（默认 src/fixtures/demo_case.json）",
    )
    parser.add_argument("--out", default=str(ROOT / "demo_output/demo_report.html"), help="输出 HTML 路径")
    parser.add_argument("--json-out", default="", help="同时输出 JSON 结果路径")
    args = parser.parse_args()

    case = load_case(args.case)
    if case.get("mode") != "demo":
        print(f"[warn] 该 case 的 mode={case.get('mode')}，不是演示数据；请确认后再展示。")

    report = build_report(case)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(report), encoding="utf-8")

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[ok] JSON 结果：{args.json_out}")

    print(f"[ok] 演示结果页：{out}")
    print(f"[info] 模式：{report.mode} ｜ 推荐方案数：{len(report.plans)} ｜ 是否建议不使用：{report.recommend_no_use}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
