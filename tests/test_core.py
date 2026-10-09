"""独立业务逻辑验证：覆盖空数据、缺失字段、过期、超预算、渠道不匹配、
试算失败、积分缺商品、真实模式不混入演示数据、正常场景。

运行：
    python -m unittest discover -s tests -v
或：
    python tests/test_core.py
"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from expiry_butler import (  # noqa: E402
    EXPIRED,
    EXPIRING,
    UNKNOWN,
    VALID,
    FAILED,
    MISSING,
    VERIFIED,
    Coupon,
    PriceResult,
    build_report,
    channel_state,
    classify_expiry,
    render_html,
)

NOW = "2026-10-09 17:40:00"


def case(**overrides):
    base = {
        "mode": "real",
        "query_time": NOW,
        "window_days": 7,
        "budget_yuan": 30.0,
        "need": {"用餐次数": "本周 1 次"},
        "store": {"store_code": "0000000", "store_name": "示例门店", "channel": "到店自取"},
        "coupons": [],
        "menu": [],
        "points": {},
        "mall_products": [],
    }
    base.update(overrides)
    return base


def verified_coupon(title="麦旋风任选", payable=990, original=1400, valid_to="2026-10-09 23:59:59", channel="到店自取"):
    return {
        "title": title,
        "coupon_id": "T1",
        "coupon_code": "C1",
        "valid_from": "2026-10-05 10:30:00",
        "valid_to": valid_to,
        "channel": channel,
        "products": [{"product_code": "9900014239", "product_name": "麦旋风任选1"}],
        "price": {
            "status": "verified",
            "payable_fen": payable,
            "original_fen": original,
            "discount_fen": original - payable,
            "delivery_fen": 0,
            "packing_fen": 0,
        },
    }


class TestExpiryClassification(unittest.TestCase):
    def test_missing_expiry_is_unknown(self):
        now = datetime(2026, 10, 9, 17, 40)
        self.assertEqual(classify_expiry(None, now), (UNKNOWN, None))
        self.assertEqual(classify_expiry("", now), (UNKNOWN, None))
        self.assertEqual(classify_expiry("不是时间", now), (UNKNOWN, None))

    def test_expired_and_expiring(self):
        now = datetime(2026, 10, 9, 17, 40)
        self.assertEqual(classify_expiry("2026-10-01 10:00:00", now)[0], EXPIRED)
        status, days = classify_expiry("2026-10-11 23:59:59", now)
        self.assertEqual(status, EXPIRING)
        self.assertEqual(days, 2)
        status, days = classify_expiry("2026-11-20 23:59:59", now)
        self.assertEqual(status, VALID)
        self.assertGreater(days, 7)

    def test_window_is_adjustable(self):
        now = datetime(2026, 10, 9, 17, 40)
        self.assertEqual(classify_expiry("2026-10-12 23:59:59", now, window_days=2)[0], VALID)
        self.assertEqual(classify_expiry("2026-10-12 23:59:59", now, window_days=10)[0], EXPIRING)

    def test_channel_state(self):
        self.assertEqual(channel_state("到店自取", "到店自取"), "match")
        self.assertEqual(channel_state("外送", "到店自取"), "mismatch")
        self.assertEqual(channel_state(None, "到店自取"), "unknown")
        self.assertEqual(channel_state("到店自取", None), "unknown")


class TestScenarios(unittest.TestCase):
    def test_no_coupons(self):
        r = build_report(case())
        self.assertTrue(r.recommend_no_use)
        self.assertEqual(r.plans, [])
        self.assertIn("没有可用权益", r.no_use_reason)

    def test_missing_expiry_field(self):
        """缺到期字段：状态为 unknown、不输出剩余天数、在页面标注，但不伪造到期日。"""
        c = verified_coupon(valid_to=None)
        r = build_report(case(coupons=[c]))
        self.assertEqual(r.rights[0].status, UNKNOWN)
        self.assertIsNone(r.rights[0].days_left)
        self.assertTrue(any("到期信息未提供" in u for u in r.unresolved))
        self.assertTrue(any("到期信息未提供" in x for x in r.plans[0].reasons))
        html_text = render_html(r)
        self.assertIn("到期信息未提供", html_text)
        self.assertNotIn("天后失效", html_text)

    def test_expired_right_excluded(self):
        c = verified_coupon(valid_to="2026-10-01 23:59:59")
        r = build_report(case(coupons=[c]))
        self.assertEqual(len(r.excluded), 1)
        self.assertEqual(r.excluded[0].status, EXPIRED)
        self.assertEqual(r.rights, [])

    def test_all_plans_over_budget(self):
        c = verified_coupon(payable=3500, original=5000)
        r = build_report(case(budget_yuan=30.0, coupons=[c]))
        self.assertEqual(r.plans, [])
        self.assertEqual(len(r.over_budget), 1)
        self.assertTrue(r.recommend_no_use)
        self.assertIn("超出本次预算", r.no_use_reason)

    def test_channel_mismatch_excluded(self):
        c = verified_coupon(channel="外送")
        r = build_report(case(coupons=[c]))
        self.assertEqual(len(r.excluded), 1)
        self.assertIn("渠道不匹配", r.excluded[0].reasons[0])
        self.assertEqual(r.plans, [])

    def test_price_calc_failed(self):
        c = verified_coupon()
        c["price"] = {"status": "failed", "error": "接口返回 500"}
        r = build_report(case(coupons=[c]))
        self.assertEqual(r.plans, [])
        self.assertEqual(len(r.over_budget), 1)
        self.assertEqual(r.over_budget[0].price_status, FAILED)
        self.assertIsNone(r.over_budget[0].price.payable)
        self.assertTrue(any("价格试算失败" in u for u in r.unresolved))

    def test_points_expiring_without_mall_products(self):
        r = build_report(
            case(
                points={"available": 500, "expiring_this_month": 300, "expiring_next_month": 0, "expire_date": None}
            )
        )
        self.assertTrue(any("缺少可兑换商品信息" in u for u in r.unresolved))
        self.assertTrue(any("具体到期日期" in u for u in r.unresolved))
        self.assertEqual(r.mall_products, [])

    def test_real_mode_never_mixes_demo_data(self):
        """真实模式下即使查询为空，也不得注入演示样例。"""
        r = build_report(case(mode="real", coupons=[], menu=[]))
        self.assertEqual(r.mode, "real")
        self.assertEqual(r.plans, [])
        html_text = render_html(r)
        self.assertNotIn("样例数据，非实时账户结果", html_text)
        self.assertIn("真实模式", html_text)

    def test_demo_mode_marked_clearly(self):
        r = build_report(case(mode="demo", coupons=[]))
        html_text = render_html(r)
        self.assertIn("样例数据，非实时账户结果", html_text)

    def test_normal_two_plans_with_traceable_price(self):
        r = build_report(
            case(
                coupons=[
                    verified_coupon(title="麦旋风任选", payable=990, original=1400),
                    verified_coupon(title="薯薯任选", payable=990, original=1400),
                    verified_coupon(title="厚松饼堡早餐", payable=3500, original=4500),
                ],
                menu=[{"code": "521951", "name": "灰焰圆筒", "current_price": "5"}],
            )
        )
        self.assertEqual(len(r.plans), 2)
        for p in r.plans:
            self.assertEqual(p.price_status, VERIFIED)
            self.assertIsNotNone(p.price.payable)
            self.assertLessEqual(p.price.payable, 30.0)
            self.assertTrue(any("官方价格试算" in x for x in p.reasons))
        # 超预算的进入 over_budget，不混入推荐
        self.assertEqual(len(r.over_budget), 1)
        self.assertFalse(r.recommend_no_use)

    def test_savings_only_when_verified(self):
        ok = PriceResult(status=VERIFIED, payable_fen=990, original_fen=1400)
        self.assertIn("省 4.10 元", ok.savings_text())
        bad = PriceResult(status=MISSING, payable_fen=990, original_fen=1400)
        self.assertIsNone(bad.savings_text())
        flat = PriceResult(status=VERIFIED, payable_fen=1400, original_fen=1400)
        self.assertIsNone(flat.savings_text())


class TestReportRendering(unittest.TestCase):
    def test_html_contains_required_sections(self):
        r = build_report(case(mode="demo", coupons=[verified_coupon()]))
        html_text = render_html(r)
        for section in [
            "本次需求与预算",
            "权益清单",
            "推荐方案",
            "不建议使用",
            "积分权益",
            "未确认条件",
            "查询时间",
        ]:
            self.assertIn(section, html_text)
        self.assertIn("viewport", html_text)  # 手机适配

    def test_no_token_like_content_in_html(self):
        r = build_report(case(mode="demo", coupons=[verified_coupon()]))
        html_text = render_html(r)
        self.assertNotIn("Bearer", html_text)
        self.assertNotIn("mcp.mcd.cn", html_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
