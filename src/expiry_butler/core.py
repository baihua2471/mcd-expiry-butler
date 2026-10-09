"""麦麦权益到期管家 —— 核心业务逻辑（纯函数，不调用任何外部接口）。

设计约束（对应产品业务原则）：
1. 预算优先于消耗权益；没有合适方案时推荐“不使用”。
2. 券面额/宣传价不等于最终应付；只有 calculate-price 成功才算“已验证”。
3. 缺少到期字段时输出“到期信息未提供”，禁止推断到期时间。
4. 积分与现金分开展示，不做任何兑换比例换算。
5. 不假设券可叠加、不假设跨门店/跨渠道通用。
6. 缺失数据不当作 0；失败不静默降级为样例数据。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

CN_TZ = ZoneInfo("Asia/Shanghai") if ZoneInfo else timezone(timedelta(hours=8))

# 到期状态
EXPIRED = "expired"        # 已过期
EXPIRING = "expiring"      # 快到期（窗口内）
VALID = "valid"            # 有效期内，但未进入窗口
UNKNOWN = "unknown"        # 到期信息未提供

# 价格状态
VERIFIED = "verified"      # 已通过官方 calculate-price 试算
FAILED = "failed"          # 试算失败
MISSING = "missing"        # 未做试算（例如仅取到菜单价）

DEFAULT_WINDOW_DAYS = 7


# --------------------------------------------------------------------------
# 基础工具
# --------------------------------------------------------------------------
def parse_dt(value: Any) -> Optional[datetime]:
    """解析接口返回的时间字符串；解析失败一律返回 None（禁止猜测）。"""
    if not value:
        return None
    text = str(value).strip().replace("T", " ")
    fmts = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")
    for fmt in fmts:
        try:
            dt = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return dt.replace(tzinfo=CN_TZ)
    return None


def ensure_cn(dt: datetime) -> datetime:
    """把时间统一成北京时间 aware datetime；naive 输入按北京时间解释。"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=CN_TZ)
    return dt.astimezone(CN_TZ)


def now_in_cn(value: Any = None) -> datetime:
    """当前时间；支持从外部传入（便于测试与复现），统一按北京时间。"""
    if isinstance(value, datetime):
        return ensure_cn(value)
    parsed = parse_dt(value)
    if parsed is not None:
        return parsed
    return datetime.now(tz=CN_TZ)


def fen_to_yuan(fen: Optional[int]) -> Optional[float]:
    if fen is None:
        return None
    return round(fen / 100.0, 2)


# --------------------------------------------------------------------------
# 数据结构
# --------------------------------------------------------------------------
@dataclass
class PriceResult:
    """一次官方价格试算的结果。单位：分。"""
    status: str = MISSING
    payable_fen: Optional[int] = None
    original_fen: Optional[int] = None
    discount_fen: Optional[int] = None
    delivery_fen: Optional[int] = None
    packing_fen: Optional[int] = None
    error: Optional[str] = None

    @property
    def payable(self) -> Optional[float]:
        return fen_to_yuan(self.payable_fen)

    @property
    def original(self) -> Optional[float]:
        return fen_to_yuan(self.original_fen)

    def savings_text(self) -> Optional[str]:
        """只有原价与应付价都来自同一次官方试算，才输出“省了 X 元”。"""
        if self.status != VERIFIED:
            return None
        if self.original_fen is None or self.payable_fen is None:
            return None
        diff = self.original_fen - self.payable_fen
        if diff <= 0:
            return None
        return f"省 {fen_to_yuan(diff):.2f} 元（相对本次试算原价）"


@dataclass
class Coupon:
    title: str
    coupon_id: Optional[str] = None
    coupon_code: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    channel: Optional[str] = None          # 到店 / 外送 / None=未标注
    products: List[Dict[str, Any]] = field(default_factory=list)
    price: PriceResult = field(default_factory=PriceResult)
    source: str = "store"                  # store=门店维度可用券 / wallet=卡包概览

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "Coupon":
        price_raw = raw.get("price") or {}
        price = PriceResult(
            status=price_raw.get("status", MISSING),
            payable_fen=price_raw.get("payable_fen"),
            original_fen=price_raw.get("original_fen"),
            discount_fen=price_raw.get("discount_fen"),
            delivery_fen=price_raw.get("delivery_fen"),
            packing_fen=price_raw.get("packing_fen"),
            error=price_raw.get("error"),
        )
        return cls(
            title=raw.get("title") or raw.get("name") or "未命名权益",
            coupon_id=raw.get("coupon_id"),
            coupon_code=raw.get("coupon_code"),
            valid_from=raw.get("valid_from"),
            valid_to=raw.get("valid_to"),
            channel=raw.get("channel"),
            products=list(raw.get("products") or []),
            price=price,
            source=raw.get("source", "store"),
        )


@dataclass
class Screened:
    coupon: Coupon
    status: str
    days_left: Optional[int]
    reasons: List[str] = field(default_factory=list)


@dataclass
class Plan:
    title: str
    items: List[Dict[str, Any]] = field(default_factory=list)
    coupon: Optional[Coupon] = None
    price: PriceResult = field(default_factory=PriceResult)
    price_status: str = MISSING
    within_budget: Optional[bool] = None
    reasons: List[str] = field(default_factory=list)
    expiry_status: str = UNKNOWN
    days_left: Optional[int] = None
    channel: Optional[str] = None
    store: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "items": self.items,
            "coupon": {
                "title": self.coupon.title,
                "coupon_id": self.coupon.coupon_id,
                "coupon_code": self.coupon.coupon_code,
                "valid_to": self.coupon.valid_to,
            } if self.coupon else None,
            "price_status": self.price_status,
            "payable_yuan": self.price.payable,
            "original_yuan": self.price.original,
            "delivery_yuan": fen_to_yuan(self.price.delivery_fen),
            "packing_yuan": fen_to_yuan(self.price.packing_fen),
            "savings": self.price.savings_text(),
            "within_budget": self.within_budget,
            "reasons": self.reasons,
            "expiry_status": self.expiry_status,
            "days_left": self.days_left,
            "channel": self.channel,
            "store": self.store,
        }


@dataclass
class Report:
    mode: str
    query_time: str
    budget: Optional[float]
    need: Dict[str, Any]
    store: Dict[str, Any]
    window_days: int
    rights: List[Screened] = field(default_factory=list)
    excluded: List[Screened] = field(default_factory=list)
    plans: List[Plan] = field(default_factory=list)
    over_budget: List[Plan] = field(default_factory=list)
    points: Dict[str, Any] = field(default_factory=dict)
    mall_products: List[Dict[str, Any]] = field(default_factory=list)
    unresolved: List[str] = field(default_factory=list)
    recommend_no_use: bool = False
    no_use_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "query_time": self.query_time,
            "budget": self.budget,
            "need": self.need,
            "store": self.store,
            "window_days": self.window_days,
            "rights": [
                {
                    "title": s.coupon.title,
                    "valid_to": s.coupon.valid_to,
                    "expiry_status": s.status,
                    "days_left": s.days_left,
                    "channel": s.coupon.channel,
                    "reasons": s.reasons,
                }
                for s in self.rights
            ],
            "excluded": [
                {
                    "title": s.coupon.title,
                    "valid_to": s.coupon.valid_to,
                    "expiry_status": s.status,
                    "days_left": s.days_left,
                    "channel": s.coupon.channel,
                    "reasons": s.reasons,
                }
                for s in self.excluded
            ],
            "plans": [p.to_dict() for p in self.plans],
            "over_budget": [p.to_dict() for p in self.over_budget],
            "points": self.points,
            "mall_products": self.mall_products,
            "unresolved": self.unresolved,
            "recommend_no_use": self.recommend_no_use,
            "no_use_reason": self.no_use_reason,
        }


# --------------------------------------------------------------------------
# 到期判定
# --------------------------------------------------------------------------
def classify_expiry(valid_to: Any, now: datetime, window_days: int = DEFAULT_WINDOW_DAYS) -> Tuple[str, Optional[int]]:
    """返回 (状态, 剩余天数)。没有到期字段时返回 (unknown, None)，绝不推断。"""
    if not valid_to:
        return UNKNOWN, None
    dt = parse_dt(valid_to)
    if dt is None:
        return UNKNOWN, None
    now = ensure_cn(now)
    days_left = (dt.date() - now.date()).days
    if dt < now:
        return EXPIRED, days_left
    if days_left <= window_days:
        return EXPIRING, days_left
    return VALID, days_left


def channel_state(coupon_channel: Optional[str], target_channel: Optional[str]) -> str:
    """渠道匹配判定：match / mismatch / unknown。未知不静默放行。"""
    if not coupon_channel or not target_channel:
        return "unknown"
    a, b = str(coupon_channel).strip(), str(target_channel).strip()
    if a == b:
        return "match"
    if a in b or b in a:
        return "match"
    return "mismatch"


def screen_coupons(
    coupons: Iterable[Coupon],
    now: datetime,
    target_channel: Optional[str],
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> Tuple[List[Screened], List[Screened]]:
    """把权益分成“可纳入方案”与“不建议使用”两组，并给出原因。"""
    usable: List[Screened] = []
    excluded: List[Screened] = []

    for c in coupons:
        status, days_left = classify_expiry(c.valid_to, now, window_days)
        reasons: List[str] = []

        if status == EXPIRED:
            excluded.append(Screened(c, status, days_left, ["已过期，不建议使用"]))
            continue

        ch = channel_state(c.channel, target_channel)
        if ch == "mismatch":
            excluded.append(
                Screened(c, status, days_left, [f"渠道不匹配：券标注「{c.channel}」，本次为「{target_channel}」"])
            )
            continue

        if status == UNKNOWN:
            reasons.append("到期信息未提供（接口未返回有效期），不参与“快到期”排序")
        if ch == "unknown":
            reasons.append("渠道未标注或未确认，需以门店维度可用券结果为准")
        if not c.products:
            reasons.append("接口未返回适用商品，无法组方案")
        if c.price.status == FAILED:
            reasons.append(f"价格试算失败：{c.price.error or '接口未返回原因'}")

        usable.append(Screened(c, status, days_left, reasons))

    return usable, excluded


# --------------------------------------------------------------------------
# 方案生成
# --------------------------------------------------------------------------
def _menu_lookup(menu: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out = {}
    for m in menu or []:
        code = str(m.get("code") or m.get("product_code") or "")
        if code:
            out[code] = m
    return out


def _item_name(code: str, menu_map: Dict[str, Dict[str, Any]], fallback: str = "") -> str:
    m = menu_map.get(str(code))
    if m and m.get("name"):
        return str(m["name"])
    return fallback or f"商品 {code}"


def build_plans(
    usable: List[Screened],
    budget: Optional[float],
    menu: List[Dict[str, Any]],
    store: Dict[str, Any],
    channel: Optional[str],
    max_plans: int = 2,
) -> Tuple[List[Plan], List[Plan]]:
    """生成最多两套方案；返回 (预算内方案, 超预算/不可用方案)。"""
    menu_map = _menu_lookup(menu)
    candidates: List[Plan] = []
    over: List[Plan] = []

    for s in usable:
        c = s.coupon
        if not c.products:
            continue

        items = []
        for p in c.products:
            code = str(p.get("product_code") or p.get("code") or "")
            if not code:
                continue
            items.append(
                {
                    "product_code": code,
                    "name": _item_name(code, menu_map, str(p.get("product_name") or "")),
                    "quantity": int(p.get("quantity") or 1),
                }
            )
        if not items:
            continue

        reasons: List[str] = list(s.reasons)
        if s.status == EXPIRING:
            reasons.insert(0, f"快到期：{s.days_left} 天后失效（{c.valid_to}）")
        elif s.status == UNKNOWN:
            reasons.insert(0, "到期信息未提供，无法判断是否为快到期权益")
        else:
            reasons.insert(0, f"有效期内：{c.valid_to}")

        price_status = c.price.status
        if price_status == VERIFIED:
            reasons.append("应付金额已通过官方价格试算（calculate-price）")
        elif price_status == FAILED:
            reasons.append("价格试算失败，不输出估算金额")
        else:
            reasons.append("未做官方价格试算，金额为菜单现价，仅供参考")

        plan = Plan(
            title=f"用「{c.title}」" + (f" · {items[0]['name']}" if len(items) == 1 else f" 等 {len(items)} 件"),
            items=items,
            coupon=c,
            price=c.price,
            price_status=price_status,
            reasons=reasons,
            expiry_status=s.status,
            days_left=s.days_left,
            channel=channel,
            store=store.get("store_name") if store else None,
        )

        payable = c.price.payable
        if price_status == VERIFIED and payable is not None:
            if budget is None or payable <= budget + 1e-9:
                plan.within_budget = True
                candidates.append(plan)
            else:
                plan.within_budget = False
                plan.reasons.append(
                    f"超预算：应付 {payable:.2f} 元 > 预算 {budget:.2f} 元"
                    if budget is not None
                    else "未设定预算"
                )
                over.append(plan)
        else:
            # 未验证 / 失败：不进入推荐，只作为不可用项展示（预算未知）
            plan.within_budget = None
            over.append(plan)

    # 排序：快到期优先 → 价格贴近预算（不超）优先 → 券名稳定排序
    def sort_key(p: Plan):
        exp_rank = 0 if p.expiry_status == EXPIRING else (1 if p.expiry_status == UNKNOWN else 2)
        days = p.days_left if p.days_left is not None else 9999
        payable = p.price.payable if p.price.payable is not None else 0.0
        gap = abs((budget or 0) - payable)
        return (exp_rank, days, gap, p.title)

    candidates.sort(key=sort_key)

    # 预算内的菜单兜底方案（不使用券），仅在不足两套时补充
    if len(candidates) < max_plans and menu and budget is not None:
        plain: List[Tuple[float, Dict[str, Any]]] = []
        for m in menu:
            try:
                price = float(m.get("current_price") or m.get("current_price_yuan") or 0)
            except (TypeError, ValueError):
                continue
            if 0 < price <= budget + 1e-9:
                plain.append((price, m))
        plain.sort(key=lambda x: -x[0])
        for price, m in plain[: max_plans - len(candidates)]:
            code = str(m.get("code") or m.get("product_code") or "")
            candidates.append(
                Plan(
                    title=f"不用券 · {m.get('name', code)}",
                    items=[{"product_code": code, "name": str(m.get("name", code)), "quantity": 1}],
                    coupon=None,
                    price=PriceResult(status=MISSING, payable_fen=int(round(price * 100))),
                    price_status=MISSING,
                    within_budget=True,
                    reasons=[
                        "不使用任何权益，按菜单现价估算",
                        "该金额为菜单展示价，未经官方价格试算，不作为最终应付金额",
                    ],
                    expiry_status=VALID,
                    days_left=None,
                    channel=channel,
                    store=store.get("store_name") if store else None,
                )
            )

    return candidates[:max_plans], over


# --------------------------------------------------------------------------
# 入口
# --------------------------------------------------------------------------
def build_report(case: Dict[str, Any]) -> Report:
    mode = case.get("mode", "real")
    now = now_in_cn(case.get("query_time"))
    window_days = int(case.get("window_days") or DEFAULT_WINDOW_DAYS)
    budget = case.get("budget_yuan")
    budget = float(budget) if budget not in (None, "") else None
    store = case.get("store") or {}
    channel = store.get("channel") or case.get("channel")

    coupons = [Coupon.from_dict(c) for c in (case.get("coupons") or [])]
    usable, excluded = screen_coupons(coupons, now, channel, window_days)
    plans, over = build_plans(
        usable, budget, case.get("menu") or [], store, channel, max_plans=int(case.get("max_plans") or 2)
    )

    unresolved: List[str] = []
    if any(s.status == UNKNOWN for s in usable + excluded):
        unresolved.append("存在未提供到期时间的权益，已标注“到期信息未提供”，未推断到期日")
    if any(channel_state(s.coupon.channel, channel) == "unknown" for s in usable):
        unresolved.append("存在渠道未标注的权益，已按门店维度可用券结果处理，未假设跨渠道通用")
    if any(p.price_status == FAILED for p in over):
        unresolved.append("至少一个方案价格试算失败，未输出估算金额")
    if any(p.price_status == MISSING for p in plans):
        unresolved.append("部分方案未做官方价格试算，金额仅来自菜单展示价")
    if budget is None:
        unresolved.append("未提供预算，未做预算匹配")

    points = dict(case.get("points") or {})
    mall_products = list(case.get("mall_products") or [])
    if points:
        if points.get("expire_date") in (None, ""):
            unresolved.append("积分账户未返回具体到期日期，仅展示“本月/下月将过期”数量")
        expiring = 0.0
        for key in ("expiring_this_month", "expiring_next_month"):
            try:
                expiring += float(points.get(key) or 0)
            except (TypeError, ValueError):
                pass
        if expiring > 0 and not mall_products:
            unresolved.append("存在即将过期积分，但缺少可兑换商品信息，未给出积分使用建议")

    recommend_no_use = not plans
    no_use_reason = None
    if recommend_no_use:
        if budget is not None and over:
            no_use_reason = "所有可验证方案均超出本次预算，不建议为了消耗权益额外消费"
        elif over and all(p.price_status == FAILED for p in over):
            no_use_reason = "价格试算失败，无法给出可信金额，不推荐使用"
        elif not coupons:
            no_use_reason = "当前门店与渠道下没有可用权益，建议按正常菜单点单"
        else:
            no_use_reason = "没有同时满足预算与有效期条件的方案，建议不使用权益"

    return Report(
        mode=mode,
        query_time=now.strftime("%Y-%m-%d %H:%M:%S"),
        budget=budget,
        need=case.get("need") or {},
        store=store,
        window_days=window_days,
        rights=usable,
        excluded=excluded,
        plans=plans,
        over_budget=over,
        points=points,
        mall_products=mall_products,
        unresolved=unresolved,
        recommend_no_use=recommend_no_use,
        no_use_reason=no_use_reason,
    )


def load_case(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
