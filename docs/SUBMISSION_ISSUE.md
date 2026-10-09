# 报名 Issue 草稿

> 在活动仓库 https://github.com/M-China/mcd-developer-innovation-challenge 用 Issue 模板提交。
> 提交前把「项目地址」占位符换成你自己的仓库地址。

---

```text
【参赛申请】
项目名称：麦麦权益到期管家
项目地址：https://github.com/<你的GitHub用户名>/mcd-expiry-butler
项目简介：券快到期了，但为了不浪费而多点 20 块真的划算吗？这个 WorkBuddy Skill 用麦当劳 MCP 只读查询你的优惠券和积分，按预算和门店给出最多两套方案，金额全部经过官方价格试算，并明确告诉你哪些权益不值得为了到期硬消费。
```

---

## 提交前检查

- [ ] 仓库为 **Public**，创建时间在活动期内（2025-12-25 ~ 2026-10-25）
- [ ] 根目录含：`README.md`、`CONTEST_DECLARATION.md`、`MCP_INTEGRATION.md`、`mcp-config.example.json`
- [ ] 参与 WorkBuddy 专项：`workbuddy.md` 已替换为**真实导出的对话上下文**
- [ ] 全库无真实 Token / 券码 / 手机号 / 收货地址（见 `workbuddy.md` 脱敏清单）
- [ ] 提交时间：北京时间 2026-10-25 23:59 前
- [ ] 同一 GitHub 账号如有多个项目，只有 Star 最高的进榜

## 附加说明（可写在 Issue 评论区，非必需）

- 真实使用 `mcd-mcp`：主链路 `now-time-info` → `query-nearby-stores` → `query-store-coupons` → `calculate-price`，并辅以积分与菜单查询
- 第一版只做只读：不领券、不兑换、不下单、不抽奖、不改地址
- 价格可追溯：所有推荐金额均经过 `calculate-price`，试算失败即标注失败，不估算
- 17 个独立逻辑用例覆盖空数据、缺字段、过期、超预算、渠道不符、试算失败等场景
