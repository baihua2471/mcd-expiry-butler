#!/usr/bin/env python3
"""生成 GitHub Pages 用的展示页：docs/index.html

内容 = 项目简介 + 演示模式结果页（样例数据）。
只用标准库，不联网，不写任何 Token 或账户数据。

用法：
    python3 scripts/build_pages.py [--out docs/index.html]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from expiry_butler.cli import load_case  # noqa: E402
from expiry_butler.core import build_report  # noqa: E402
from expiry_butler.report import render_html  # noqa: E402

REPO_URL = "https://github.com/baihua2471/mcd-expiry-butler"

EXTRA_CSS = """
.intro{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px;margin-bottom:14px}
.intro h2{margin:0 0 8px;border:0;padding:0;font-size:16px}
.intro p{margin:0 0 10px;font-size:14px;line-height:1.7}
.feat{margin:0;padding:0;list-style:none;font-size:13px;color:var(--muted)}
.feat li{padding-left:18px;position:relative;margin:6px 0;line-height:1.6}
.feat li::before{content:"";position:absolute;left:4px;top:9px;width:6px;height:6px;
  border-radius:50%;background:var(--accent)}
.cta{display:block;margin-top:14px;padding:11px 14px;border-radius:10px;text-align:center;
  background:var(--accent);color:#fff;text-decoration:none;font-size:14px;font-weight:600}
.cta.plain{background:#eef0f3;color:var(--ink);font-weight:500;margin-top:8px}
.cta:hover{opacity:.9}
.meta{font-size:12px;color:var(--muted);margin-top:10px;line-height:1.6}
"""

HEADER = f"""
  <div class="intro">
    <h2>这是什么</h2>
    <p>一个真实使用麦当劳官方 MCP 的 WorkBuddy Skill。它只读查询你快到期的优惠券和积分，
       按你给的预算给出最多两套用餐方案，金额全部经过官方价格试算——然后明确告诉你，
       <b>哪些权益不值得为了到期而硬消费</b>。</p>
    <ul class="feat">
      <li>预算优先于消耗权益：没有合适方案时，会直接建议你这次别用</li>
      <li>金额必须官方试算，不用券面额或估算冒充实付价</li>
      <li>缺什么数据就标「未提供」，不猜、不补、不把缺失当 0</li>
      <li>第一版只做查询与试算：不领券、不兑换、不下单</li>
    </ul>
    <div class="meta">下面是<b>演示模式</b>的输出样例（样例数据，非任何真实账户结果）。
       真实使用时由你在 WorkBuddy 里用中文提问，走你自己的 MCP 连接器查询。</div>
    <a class="cta" href="{REPO_URL}">查看源码与安装方法 →</a>
    <a class="cta plain" href="{REPO_URL}/blob/main/MCP_INTEGRATION.md">看看它到底调了哪些 MCP 工具</a>
  </div>
"""

FOOTER = f"""
  <div class="foot">
    <a href="{REPO_URL}">GitHub 仓库</a> ·
    <a href="{REPO_URL}/blob/main/README.md">安装说明</a> ·
    <a href="{REPO_URL}/blob/main/MCP_INTEGRATION.md">MCP 集成说明</a><br>
    本项目为参加「麦当劳程序员创意开发大赛」的个人原创作品，<b>非麦当劳官方产品，不代表官方背书</b>。<br>
    页面不使用任何品牌 Logo 或未经授权的素材，不含任何 Token、账号或隐私信息。
  </div>
"""


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default=os.path.join(root, "src", "fixtures", "demo_case.json"))
    ap.add_argument("--out", default=os.path.join(root, "docs", "index.html"))
    args = ap.parse_args()

    with open(args.case, "r", encoding="utf-8") as f:
        case = json.load(f)

    report = build_report(case)
    html = render_html(report)

    # 注入展示页专属样式、头部简介与底部链接
    html = html.replace("</style>", EXTRA_CSS + "</style>", 1)
    html = html.replace('<div class="wrap">', "<div class=\"wrap\">" + HEADER, 1)
    html = html.replace("</body>", FOOTER + "</body>", 1)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 已生成 {os.path.relpath(args.out, root)}（{len(html)} 字节）")
    print(f"   模式：{report.mode} · 方案数：{len(report.plans)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
