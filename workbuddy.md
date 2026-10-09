# workbuddy.md

> 本文件用于「麦当劳程序员创意开发大赛 · WorkBuddy 专项奖励」。
> 规则要求提交「WorkBuddy 对话上下文」，`workbuddy.md` 即为该材料。

---

## ⚠️ 当前状态：待替换为真实对话导出

**本文件目前不是提交用的最终内容**，而是一份占位说明 + 导出指引。

原因：对话上下文只能由 WorkBuddy 客户端导出，我不代写、不生成假的对话记录，
也不用「总结」冒充完整开发记录（那不符合活动对 `workbuddy.md` 的要求）。

**提交前必须由你本人完成替换。**

---

## 导出步骤（请按你使用的 WorkBuddy 版本选择）

1. **优先用官方导出入口**：在本次开发会话的界面中查找「导出会话 / 导出对话 / Export」之类的入口，
   选择 Markdown 格式，保存为仓库根目录的 `workbuddy.md`。
2. **没有导出入口时**：全选会话内容复制，粘贴进 `workbuddy.md`，保持时间顺序，不要改写。
3. **最小可接受版本**：如果只能导出片段，至少包含本次开发的完整主线：
   接口能力检查 → 真实只读联调 → 实现 → 验证 → 文档。

导出后请确认文件里**确实包含多轮问答**，而不是只有一段总结。

---

## 公开前脱敏检查清单（逐项打勾）

- [ ] 全文搜索 `Bearer`：不应出现真实 Token（出现即删除，替换为 `Bearer <已脱敏>`）
- [ ] 搜索券码特征（形如 `MCD` + 字母数字的长串）与券ID（32 位十六进制）：不应出现真实值
- [ ] 搜索 `mcp-approvals`、`~/.workbuddy/mcp.json`：本地路径中若含 Token 需脱敏
- [ ] 搜索手机号、收货地址、真实姓名：不应出现
- [ ] 搜索纯数字门店编号（7 位左右）：如认为属于隐私，替换为 `<门店编号已脱敏>`
- [ ] 搜索 `accountId`、`traceId`：替换为 `<已脱敏>`
- [ ] 确认 `mcp-config.example.json` 中只有 `${MCD_MCP_TOKEN}` 占位符
- [ ] 确认 `demo_output/*.html`、`src/fixtures/*.json` 中无真实券码

一条命令自检（在仓库根目录执行）：

```bash
grep -rInE "Bearer [A-Za-z0-9]{8,}|1[0-9A-Za-z]{20,}|1\d{10}" --exclude-dir=.git . || echo "未发现疑似凭证"
```

---

## 本次开发的真实主线（用于核对导出内容是否完整，不是对话记录本身）

1. 检查 WorkBuddy 是否已连接麦当劳 MCP —— 否，官方有远程 MCP（`open.mcd.cn`），需用户自申请 Token
2. 配置 MCP：写 `~/.workbuddy/mcp.json`，并登记信任记录 `mcp-approvals.json`，重启后连通（35 个工具）
3. 抓取活动规则与 `CONTEST_DECLARATION.md`（原样保留）
4. 真实只读联调：`now-time-info` / `query-nearby-stores` / `query-store-coupons` /
   `query-my-coupons` / `query-my-account` / `mall-points-products` /
   `query-meals` / `query-meal-detail` / `calculate-price`
5. 依据真实返回确定功能边界（详见 `MCP_INTEGRATION.md` 第 5 节）
6. 实现 Skill（`SKILL.md`）+ 核心逻辑（`src/expiry_butler/`）+ 结果页
7. 写 17 个用例并全部通过；生成演示页与真实联调脱敏页
8. 补齐 README / MCP_INTEGRATION / mcp-config.example.json / CONTEST_DECLARATION / .gitignore / 演示脚本 / 报名草稿

如果你的导出内容缺少其中某一步，说明导出不完整，请重新导出更长的时间范围。
