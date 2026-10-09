# MCP 集成说明（MCP_INTEGRATION.md）

## 1. 使用的 MCP Server

| 项 | 值 |
|---|---|
| 服务名称 | `mcd-mcp`（麦当劳中国官方 MCP Server） |
| 官方文档 | https://github.com/M-China/mcd-mcp-server |
| 传输协议 | Streamable HTTP |
| 接入地址 | `https://mcp.mcd.cn/mcp-servers/mcd-mcp` |
| 鉴权 | `Authorization: Bearer <用户在 open.mcd.cn 自行申请的 Token>` |
| 客户端 | 腾讯 WorkBuddy（用户自己的连接器，Token 只存在本地） |
| 配置示例 | `mcp-config.example.json`（仅环境变量占位符） |

本项目**不代理、不转发、不托管任何用户 Token**，也不提供公共 Token 服务。

---

## 2. 实际使用的工具与调用流程

### 2.1 工具清单（以真实连接器返回为准）

| 工具 | 用途 | 关键返回字段 | 联调状态 |
|---|---|---|---|
| `now-time-info` | 取服务器时间作为「查询时间」 | `datetime` | ✅ 已验证 |
| `query-nearby-stores` | 查可选门店 | `storeCode / storeName / address / reservationTimeOptions` | ✅ 已验证 |
| `query-store-coupons` | **主数据源**：门店+渠道维度可用券 | `title / couponId / couponCode / tradeDateTime / products[].productCode` | ✅ 已验证 |
| `calculate-price` | 官方价格试算 | `productOriginalPrice / productPrice / discount / price / deliveryPrice / packingPrice`（单位：分） | ✅ 已验证 |
| `query-my-coupons` | 卡包概览 | 券名 / 用券价 / 有效期 / 渠道标签 | ✅ 已验证（无 `couponId`，仅作对照） |
| `query-my-account` | 积分账户 | `availablePoint / currentMouthExpirePoint / nextMouthExpirePoint` | ✅ 已验证 |
| `mall-points-products` | 积分可兑换商品 | `spuId / point / downTime / status` | ✅ 已验证 |
| `query-meals` | 菜单与现价 | `categories / meals{currentPrice, originalPrice, discountType}` | ✅ 已验证 |
| `query-meal-detail` | 套餐组成与选配 | `rounds[].choices` | ✅ 已验证（无价格字段） |

未使用（第一版红线，明确禁止调用）：
`auto-bind-coupons`、`mall-create-order`、`create-order`、`cancel-order`、`draw-lottery`、`party-order-create`、`delivery-create-address`。

### 2.2 调用流程

```
用户提出需求（预算 / 就餐方式 / 门店 / 忌口）
        │
        ├─ now-time-info ─────────────→ 查询时间（北京时间）
        ├─ query-nearby-stores ───────→ 门店列表 → 用户选门店 → storeCode
        ├─ query-store-coupons ───────→ 该门店+渠道可用券（含 couponId / 有效期 / 适用商品）
        ├─ query-my-coupons ──────────→ 卡包概览对照（无 couponId，不用于试算）
        ├─ query-my-account ──────────→ 积分余额与将过期数量
        ├─ mall-points-products ──────→ 可选兑换（仅有将过期积分时）
        ├─ query-meals ───────────────→ 菜单现价（无券备选 / 原价对照）
        └─ calculate-price × N ───────→ 每个候选方案的实际应付（带 couponId + couponCode）
                    │
        case JSON（结构化结果）
                    │
        src/expiry_butler/core.py  ──→ 到期判定 / 渠道匹配 / 预算筛选 / 方案排序
        src/expiry_butler/report.py ─→ 单文件 HTML 结果页
```

---

## 3. 真实联调记录（2026-10-09，只读，已脱敏）

详见 `docs/REAL_RUN_2026-10-09.md`。摘要：

| 调用 | 结果 |
|---|---|
| `now-time-info` | 返回 `2026-10-09 17:34:53` 周五（GMT+08:00） |
| `query-nearby-stores`（searchType=1） | 返回 `600050 收藏餐厅列表为空`，改用 `searchType=2 + city + keyword` 成功 |
| `query-store-coupons` | 卡包 14 张券，该门店+到店渠道下**仅 2 张可用**，返回 `couponId / couponCode / tradeDateTime / products` |
| `calculate-price`（带券试算） | `productOriginalPrice=1400`、`price=990`、`discount=410`（分）→ 应付 **¥9.90**（已验证） |
| `query-my-account` | `availablePoint=0`，`currentMouthExpirePoint=0`，**不返回具体到期日期** |
| `mall-points-products` | 返回 `point / downTime / status`；存在 `downTime` 已过但 `status=2` 的数据不一致 |
| `query-meals` / `query-meal-detail` | 菜单含 `currentPrice`；`query-meal-detail` **无价格字段** |

脱敏快照：`src/fixtures/real_case_sanitized.json`（券ID/券码/门店编号已替换为占位值，价格字段保留真实数值）。
复现命令：

```bash
PYTHONPATH=src python3 -m expiry_butler.cli \
  --case src/fixtures/real_case_sanitized.json \
  --out demo_output/real_run_report.html
```

---

## 4. 业务价值

1. **把「到期焦虑」变成可执行判断**：接口给出的是有效期与面额，用户真正要的是「值不值得为了它消费」。
2. **价格可追溯**：所有推荐金额都经过 `calculate-price`，不是券面额、不是宣传价，也不是模型估算。
3. **拒绝为了消耗而消费**：预算内没有合适方案时，明确输出「建议不使用」，并解释原因。
4. **门店与渠道正确性**：以门店维度的可用券为准，避免「卡包里有但这家店用不了」的误判。
5. **缺失即标注**：到期字段缺失、渠道未标注、试算失败，一律如实呈现，不做补全。

---

## 5. 接口能力边界（诚实清单）

| 问题 | 结论 |
|---|---|
| 券是否返回到期时间 | ✅ `query-store-coupons.tradeDateTime`（精确到秒，含起止） |
| 券是否返回适用门店 | ⚠️ 不直接返回适用范围，需按门店调用 `query-store-coupons` 判定 |
| 券是否返回渠道 | ⚠️ `query-my-coupons` 有「到店专用/外送专用」标签；门店维度结果本身即渠道维度结果 |
| 积分是否返回到期数量 | ✅ 本月/下月将过期数量 |
| 积分是否返回具体到期日期 | ❌ 接口未提供，页面显示「到期信息未提供」 |
| 是否能查询适用商品 | ✅ `products[].productCode` |
| 是否能拿到券后应付金额 | ✅ `calculate-price.price`（分） |
| 是否包含配送费/打包费 | ✅ `deliveryPrice / packingPrice`（外送场景才有值） |
| 兑换商品详情是否够用 | ✅ `point / downTime / status` 足以支撑「是否值得换」的判断（但不换算现金价值） |
