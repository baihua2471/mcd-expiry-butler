"""麦麦权益到期管家（mcd-expiry-butler）。

- core：到期判定、渠道匹配、预算筛选、方案生成（纯逻辑，可独立测试）
- report：单文件 HTML 结果页渲染
"""

from .core import (  # noqa: F401
    CN_TZ,
    DEFAULT_WINDOW_DAYS,
    EXPIRED,
    EXPIRING,
    UNKNOWN,
    VALID,
    FAILED,
    MISSING,
    VERIFIED,
    Coupon,
    Plan,
    PriceResult,
    Report,
    Screened,
    build_plans,
    build_report,
    channel_state,
    classify_expiry,
    fen_to_yuan,
    load_case,
    now_in_cn,
    parse_dt,
    screen_coupons,
)
from .report import render_html  # noqa: F401

__version__ = "1.0.0"
