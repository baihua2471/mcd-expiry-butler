# 麦麦权益到期管家（mcd-expiry-butler）

> 看看哪些麦当劳权益快到期，哪些值得用，哪些不用为了到期硬消费。

一个真实使用**麦当劳 MCP** 的 WorkBuddy Skill：只读查询你的优惠券与积分，按预算给出**最多两套**用餐方案，
金额全部经过官方 `calculate-price` 试算，并明确告诉你哪些权益**不值得**为了消耗而额外花钱。

---

## 一句话定位

**预算优先于消耗权益。** 没有合适方案时，它会直接说「这次别用」。

---

## 目标用户

- 卡包里攒了一堆券，每次点单前都要翻半天的人
- 被「今日到期」提示催着下单，事后发现并不划算的人
- 有预算约束（比如这周只吃一次、只花 30 元），想吃得明白的人

---

## 它做什么 / 不做什么

**做：**
- 列出快到期权益（默认 7 天窗口，可调）与有效期、剩余天数
- 按门店 + 渠道筛选真正可用的券
- 对每个候选方案调用官方价格试算，给出**已验证**应付金额
- 输出最多两套方案 + 推荐理由 + 不建议使用清单 + 未确认条件
- 积分与现金分开展示（不做任何兑换比例换算）

**不做（第一版红线）：**
- ❌ 领券 / 兑换 / 抽奖 / 下单 / 取消订单 / 付款 / 改地址
- ❌ 估算或编造价格；试算失败就显示失败
- ❌ 推断缺失的到期时间；缺就写「到期信息未提供」
- ❌ 假设券可叠加、跨门店或跨渠道通用

---

## 目录结构

```
mcd-expiry-butler/
├── README.md                     本文件
├── CONTEST_DECLARATION.md        参赛声明（取自官方仓库，原样保留）
├── MCP_INTEGRATION.md            MCP 工具、调用流程、联调状态
├── mcp-config.example.json       脱敏配置（仅环境变量占位符）
├── workbuddy.md                  WorkBuddy 专项材料说明
├── skill/mcd-expiry-butler/
│   └── SKILL.md                  Skill 本体（工作流与规则）
├── src/expiry_butler/
│   ├── core.py                   到期判定 / 渠道匹配 / 预算筛选 / 方案生成
│   ├── report.py                 单文件 HTML 结果页渲染
│   └── cli.py                    命令行入口
├── src/fixtures/
│   ├── demo_case.json            演示样例（标注为样例数据）
│   └── real_case_sanitized.json  真实联调脱敏快照
├── scripts/
│   ├── install_skill.sh          安装到 WorkBuddy
│   └── run_demo.py               演示模式
├── tests/test_core.py            17 个独立逻辑用例
├── demo_output/                  生成的结果页（可截图）
├── docs/                         联调记录、演示脚本、报名草稿
└── examples/sample-requests.md   可直接复制的示例请求
```

---

## 安装

### 前置条件

1. 已在 https://open.mcd.cn/mcp 用手机号登录并**激活 MCP Token**
2. 已把麦当劳 MCP 配到 WorkBuddy：

```json
{
  "mcpServers": {
    "mcd-mcp": {
      "type": "streamableHttp",
      "url": "https://mcp.mcd.cn/mcp-servers/mcd-mcp",
      "headers": { "Authorization": "Bearer 你的Token" }
    }
  }
}
```

配置位置：`~/.workbuddy/mcp.json`（WorkBuddy 的用户级自定义 MCP 配置）。
配好后需在**连接器管理 → 自定义连接器**中信任该服务，并**重启 WorkBuddy**。
`mcp-config.example.json` 只含 `${MCD_MCP_TOKEN}` 占位符，WorkBuddy **不会**自动展开，
请手工替换，且不要把替换后的文件提交到任何仓库。

### 安装 Skill

```bash
git clone <你的仓库地址> mcd-expiry-butler
cd mcd-expiry-butler
bash scripts/install_skill.sh
```

安装到 `~/.workbuddy/skills/mcd-expiry-butler`（加 `--project` 可装到当前项目）。
重新执行同一条命令即可更新。

依赖：Python 3.9+，仅标准库，无需 pip install。

---

## 在 WorkBuddy 里使用

直接用自然语言提问即可，Skill 会自动接管：

> 我这周只准备吃一次麦当劳，预算 30 元，看看有什么快到期的权益值得用。

它会先问清三件事（**预算 / 就餐方式 / 门店**），然后查数据、试算价格、生成结果页。

也可以直接点名：

> 用麦麦权益到期管家看看我到期的券。

### 演示模式（不需要真实账号）

```bash
cd ~/.workbuddy/skills/mcd-expiry-butler
python3 scripts/run_demo.py --out /tmp/mcd_demo.html
```

输出的页面顶部有醒目横幅：**「样例数据，非实时账户结果」**。
真实查询失败时**不会**静默切换为样例数据。

---

## 示例请求

见 `examples/sample-requests.md`，三条可直接复制：

1. `我这周只准备吃一次麦当劳，预算 30 元，看看有什么快到期的权益值得用。`
2. `帮我看看哪些券 3 天内到期，在深圳科技园到店吃，预算 25 元。`
3. `我的积分快过期了，用麦麦权益到期管家看看要不要换，别推荐我为了积分多花钱。`

---

## 验证

```bash
python3 tests/test_core.py
```

17 个用例，覆盖：

| 场景 | 期望 |
|---|---|
| 没有优惠券 | 建议不使用，说明原因 |
| 没有到期字段 | 显示「到期信息未提供」，不输出剩余天数，不推断 |
| 已过期权益 | 进入「不建议使用」，不参与推荐 |
| 所有方案超预算 | 不推荐，列出实际金额与差额 |
| 门店/渠道不适用 | 排除并说明原因 |
| 价格试算失败 | 不输出估算金额，标记为失败 |
| 积分将过期但缺兑换商品信息 | 不给积分建议，标注缺失 |
| 真实模式失败 | 不混入演示数据，模式标识保持 real |
| 正常场景 | 最多两套，价格均为「已验证」且可追溯 |

真实联调记录见 `docs/REAL_RUN_2026-10-09.md`（只读，已脱敏）。

---

## 限制

- 第一版**只做查询与试算**，不会替你领券、下单或兑换。
- 券的适用范围以**门店维度**接口结果为准；卡包概览里的券不一定在该店可用。
- 积分接口**不返回具体到期日期**，只有「本月/下月将过期」数量。
- 早餐券等带时段的券，只在对应时段可用；当前时段不符时不会推荐。
- 价格是**查询那一刻**的结果，实际下单可能因库存、时段变化而不同。
- 餐品、价格、权益与供应状态以麦当劳官方渠道实时结果为准。

---

## 免责

本项目为参赛作品，由个人独立开发，**非麦当劳官方产品**，不代表官方背书。
页面不使用任何品牌 Logo 或未经授权的素材；输出仅供参考。

---

## 开源协议

MIT License，见 [LICENSE](./LICENSE)。

协议不适用于麦当劳 MCP 服务本身，使用该服务时请遵守官方
[MCP 服务规则](https://cdn.mcd.cn/cms/pages/MCPServerRules.html)。
