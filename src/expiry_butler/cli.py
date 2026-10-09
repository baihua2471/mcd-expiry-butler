"""命令行入口：把一次查询结果（case JSON）渲染为结果页。

用法：
    python -m expiry_butler.cli --case path/to/case.json --out out.html
    python -m expiry_butler.cli --case path/to/case.json --json-only

说明：本入口只做“计算 + 渲染”，不调用任何外部接口。
MCP 查询由 Skill 流程中的智能体完成，结果写入 case JSON 后交给本入口。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .core import build_report, load_case
from .report import render_html


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="麦麦权益到期管家：结果计算与展示页生成")
    parser.add_argument("--case", required=True, help="查询结果 JSON 文件路径")
    parser.add_argument("--out", help="输出 HTML 路径（缺省时打印到 stdout）")
    parser.add_argument("--json-out", help="同时输出结构化 JSON 结果路径")
    parser.add_argument("--json-only", action="store_true", help="只输出 JSON，不生成 HTML")
    args = parser.parse_args(argv)

    case = load_case(args.case)
    report = build_report(case)

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[ok] JSON 结果已写入 {args.json_out}")

    if args.json_only:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return 0

    html_text = render_html(report)
    if args.out:
        Path(args.out).write_text(html_text, encoding="utf-8")
        print(f"[ok] 结果页已写入 {args.out}  （模式：{report.mode}）")
    else:
        sys.stdout.write(html_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
