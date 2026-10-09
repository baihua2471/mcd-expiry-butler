"""结果展示页渲染：单文件 HTML，无外部依赖，桌面与手机可读。

不使用任何品牌 Logo 或未经授权的素材，页面中的“麦当劳”仅为事实描述。
"""

from __future__ import annotations

import html
from typing import Any, Dict, List

from .core import (  # noqa: F401
    EXPIRED,
    EXPIRING,
    UNKNOWN,
    VALID,
    FAILED,
    MISSING,
    VERIFIED,
    Report,
    fen_to_yuan,
)

STATUS_TEXT = {
    EXPIRING: "快到期",
    EXPIRED: "已过期",
    VALID: "有效期内",
    UNKNOWN: "到期信息未提供",
}

PRICE_TEXT = {
    VERIFIED: "已验证（官方试算）",
    FAILED: "试算失败",
    MISSING: "未试算（菜单价）",
}

CSS = """
:root{
  --bg:#f6f7f9; --card:#ffffff; --ink:#1f2328; --muted:#6b7280;
  --line:#e5e7eb; --accent:#2f6f4f; --accent-soft:#e8f3ec;
  --warn:#8a5a00; --warn-soft:#fdf3e2; --danger:#a33a3a; --danger-soft:#fbeaea;
}
*{box-sizing:border-box}
body{margin:0;padding:20px 14px 48px;background:var(--bg);color:var(--ink);
  font:15px/1.65 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;}
.wrap{max-width:760px;margin:0 auto}
h1{font-size:21px;margin:0 0 4px}
h2{font-size:16px;margin:26px 0 10px;padding-left:10px;border-left:3px solid var(--accent)}
.sub{color:var(--muted);font-size:13px;margin:0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:14px}
.banner{border-radius:12px;padding:12px 14px;margin-bottom:16px;font-size:13px;font-weight:600}
.banner.demo{background:var(--warn-soft);color:var(--warn);border:1px dashed #d9a441}
.banner.real{background:var(--accent-soft);color:var(--accent)}
.kv{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:13px;color:var(--muted)}
.kv b{color:var(--ink);font-weight:600}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:8px 6px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:600}
.tag{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;background:#eef0f3;color:#444}
.tag.soon{background:var(--warn-soft);color:var(--warn)}
.tag.ok{background:var(--accent-soft);color:var(--accent)}
.tag.bad{background:var(--danger-soft);color:var(--danger)}
.plan{border:1px solid var(--line);border-radius:12px;padding:14px;margin-bottom:12px;background:#fff}
.plan .title{font-weight:700;margin-bottom:6px}
.price{font-size:22px;font-weight:700;color:var(--accent)}
.price small{font-size:12px;font-weight:500;color:var(--muted);margin-left:6px}
ul{margin:6px 0 0;padding-left:20px}
li{margin:3px 0}
.none{background:var(--warn-soft);border:1px dashed #d9a441;color:var(--warn);
  border-radius:12px;padding:14px;font-size:14px}
.foot{color:var(--muted);font-size:12px;margin-top:26px;border-top:1px solid var(--line);padding-top:12px}
@media (max-width:520px){
  body{padding:14px 10px 36px}
  .price{font-size:20px}
  table{font-size:12px}
  th:nth-child(3),td:nth-child(3){display:none}
}
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<div class="wrap">
  <h1>麦麦权益到期管家</h1>
  <p class="sub">看看哪些权益快到期、哪些值得用、哪些不用硬消费</p>
  {banner}
  <div class="card">
    <div class="kv">
      <span>查询时间：<b>{query_time}</b>（北京时间）</span>
      <span>快到期窗口：<b>{window_days} 天</b></span>
      <span>数据来源：<b>{mode_text}</b></span>
    </div>
  </div>

  <h2>本次需求与预算</h2>
  <div class="card">
    <div class="kv">
      <span>预算：<b>{budget}</b></span>
      <span>就餐方式：<b>{channel}</b></span>
      <span>门店：<b>{store}</b></span>
    </div>
    {need_html}
  </div>

  <h2>权益清单</h2>
  {rights_html}

  <h2>推荐方案</h2>
  {plans_html}

  <h2>不建议使用</h2>
  {excluded_html}

  <h2>积分权益（与现金分开）</h2>
  {points_html}

  <h2>未确认条件</h2>
  {unresolved_html}

  <div class="foot">
    本页由「麦麦权益到期管家」生成本地结果，非麦当劳官方产品，不代表官方背书。<br>
    餐品、价格、权益与供应状态以麦当劳官方渠道实时结果为准；金额单位：元。<br>
    页面不含任何 Token、账号或隐私信息。
  </div>
</div>
</body>
</html>
"""


def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _money(value: Any) -> str:
    if value is None:
        return "—"
    return f"{float(value):.2f}"


def _status_tag(status: str, days_left: Any = None) -> str:
    text = STATUS_TEXT.get(status, status)
    cls = {"expiring": "soon", "expired": "bad", "valid": "ok"}.get(status, "")
    if status == EXPIRING and days_left is not None:
        text = f"{text} · {days_left} 天"
    return f'<span class="tag {cls}">{_esc(text)}</span>'


def _rights_table(items: List[Any], empty_text: str) -> str:
    if not items:
        return f'<div class="card">{_esc(empty_text)}</div>'
    rows = []
    for s in items:
        c = s.coupon
        products = "、".join(
            str(p.get("product_name") or p.get("name") or p.get("product_code") or "")
            for p in (c.products or [])
        ) or "接口未返回适用商品"
        rows.append(
            "<tr>"
            f"<td><b>{_esc(c.title)}</b></td>"
            f"<td>{_esc(c.valid_to) if c.valid_to else '<i>到期信息未提供</i>'}</td>"
            f"<td>{_esc(products)}</td>"
            f"<td>{_esc(c.channel) if c.channel else '<i>未标注</i>'}</td>"
            f"<td>{_status_tag(s.status, s.days_left)}</td>"
            "</tr>"
        )
    return (
        '<div class="card"><table>'
        "<thead><tr><th>权益</th><th>有效期至</th><th>适用商品</th><th>渠道</th><th>状态</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
    )


def _plan_card(plan: Any, index: int) -> str:
    items = "、".join(f"{_esc(i.get('name'))} ×{i.get('quantity', 1)}" for i in plan.items) or "—"
    price = plan.price
    price_line = f'<div class="price">{_money(price.payable)} 元<small>{PRICE_TEXT.get(plan.price_status, plan.price_status)}</small></div>'
    if plan.price_status == FAILED:
        price_line = '<div class="price">金额不可用<small>价格试算失败，不输出估算</small></div>'
    detail = []
    if price.original is not None:
        detail.append(f"原价 {_money(price.original)} 元")
    if price.delivery_fen:
        detail.append(f"配送费 {_money(fen_to_yuan(price.delivery_fen))} 元")
    if price.packing_fen:
        detail.append(f"打包费 {_money(fen_to_yuan(price.packing_fen))} 元")
    if price.savings_text():
        detail.append(price.savings_text())
    reasons = "".join(f"<li>{_esc(r)}</li>" for r in plan.reasons)
    return (
        f'<div class="plan"><div class="title">方案 {index}：{_esc(plan.title)}</div>'
        f'<div class="kv"><span>内容：{items}</span></div>'
        f'{price_line}'
        f'<div class="kv"><span>{" · ".join(detail) if detail else "无可追溯的价格明细"}</span></div>'
        f'<div class="kv"><span>渠道：{_esc(plan.channel) if plan.channel else "未标注"}'
        f' · 门店：{_esc(plan.store) if plan.store else "未提供"}</span></div>'
        f"<ul>{reasons}</ul></div>"
    )


def render_html(report: Report) -> str:
    mode = report.mode
    is_demo = mode == "demo"
    banner = (
        '<div class="banner demo">样例数据，非实时账户结果 —— 演示模式输出，不代表任何真实账户权益</div>'
        if is_demo
        else '<div class="banner real">真实模式：数据来自你的麦当劳 MCP 连接器（只读查询）</div>'
    )

    need = report.need or {}
    need_html = ""
    if need:
        need_html = "<div class='kv'>" + "".join(
            f"<span>{_esc(k)}：<b>{_esc(v)}</b></span>" for k, v in need.items()
        ) + "</div>"

    rights_html = _rights_table(report.rights or report.excluded, "当前门店与渠道下没有查询到可用权益。")
    excluded_html = _rights_table(report.excluded, "没有需要排除的权益。")
    if report.excluded:
        extra = "".join(
            f"<li><b>{_esc(s.coupon.title)}</b>：{'；'.join(_esc(r) for r in s.reasons)}</li>"
            for s in report.excluded
        )
        excluded_html += f'<div class="card"><ul>{extra}</ul></div>'

    if report.plans:
        plans_html = "".join(_plan_card(p, i + 1) for i, p in enumerate(report.plans))
    else:
        plans_html = (
            f'<div class="none"><b>建议：本次不使用权益。</b><br>{_esc(report.no_use_reason or "")}</div>'
        )
        if report.over_budget:
            plans_html += "".join(_plan_card(p, i + 1) for i, p in enumerate(report.over_budget))

    points = report.points or {}
    if points:
        pt_rows = [
            f"<span>可用积分：<b>{_esc(points.get('available'))}</b></span>",
            f"<span>本月将过期：<b>{_esc(points.get('expiring_this_month'))}</b></span>",
            f"<span>下月将过期：<b>{_esc(points.get('expiring_next_month'))}</b></span>",
            f"<span>具体到期日期：<b>{_esc(points.get('expire_date')) if points.get('expire_date') else '到期信息未提供'}</b></span>",
        ]
        points_html = f'<div class="card"><div class="kv">{"".join(pt_rows)}</div>'
        if report.mall_products:
            rows = "".join(
                f"<tr><td>{_esc(m.get('name'))}</td><td>{_esc(m.get('point'))} 分</td>"
                f"<td>{_esc(m.get('down_time') or '到期信息未提供')}</td></tr>"
                for m in report.mall_products
            )
            points_html += (
                "<table style='margin-top:10px'><thead><tr><th>可兑换</th><th>所需积分</th>"
                f"<th>兑换截止</th></tr></thead><tbody>{rows}</tbody></table>"
            )
        else:
            points_html += '<p class="sub" style="margin-top:8px">未提供可兑换商品信息，因此不给出积分使用建议。</p>'
        points_html += '<p class="sub" style="margin-top:8px">积分与现金分别展示，本工具不设定任何兑换比例。</p></div>'
    else:
        points_html = '<div class="card">本次未查询积分账户。</div>'

    unresolved_html = (
        "<div class='card'><ul>" + "".join(f"<li>{_esc(u)}</li>" for u in report.unresolved) + "</ul></div>"
        if report.unresolved
        else '<div class="card">无。本次查询所需字段均已返回。</div>'
    )

    store = report.store or {}
    return HTML_TEMPLATE.format(
        title="麦麦权益到期管家 · 结果",
        css=CSS,
        banner=banner,
        query_time=_esc(report.query_time),
        window_days=_esc(report.window_days),
        mode_text="样例数据（演示模式）" if is_demo else "麦当劳 MCP 实时查询",
        budget=_money(report.budget) + " 元" if report.budget is not None else "未提供",
        channel=_esc(store.get("channel") or "未提供"),
        store=_esc(store.get("store_name") or store.get("store_code") or "未提供"),
        need_html=need_html,
        rights_html=rights_html,
        plans_html=plans_html,
        excluded_html=excluded_html,
        points_html=points_html,
        unresolved_html=unresolved_html,
    )
