# workbuddy.md

> 本文件用于「麦当劳程序员创意开发大赛 · WorkBuddy 专项奖励」。
> 规则要求提交「WorkBuddy 对话上下文」，`workbuddy.md` 即为该材料。

---

## ⚠️ 当前状态：占位说明，提交前必须由你替换

本文件现在**不是**提交用的对话上下文，而是"怎么生成它"的说明。

**先说清楚一个事实：当前桌面客户端没有「一键导出为 Markdown」按钮。**
依据（2026-10-10 实测）：

- 在 `/Applications/WorkBuddy.app/Contents/Resources/app.asar` 内检索
  `workbuddy.md`、`导出对话`、`导出会话`、`exportChat`、`exportAsMarkdown` —— 命中 0 次；
- 官方文档「任务对话」页列出的**顶部操作只有 4 个**：对话内搜索 / 分享任务 / 历史提问 / 显示详情面板。

所以下面给出三条真实可行的路子，按推荐度排序。

---

## 路线 A（推荐）：官方「分享任务」生成公开链接

这是客户端**确实支持**的能力，也是最稳的凭证。

1. 回到本次开发会话（就是从"当前有接入麦当劳的 MCP 吗"开始的那条）。
2. 点对话区**右上角 / 顶部的「分享任务」**。
3. 等待生成**公开链接**，复制它。
4. 把链接贴进本文件（见下方"最终文件应有的样子"），
   **同时在 README 顶部加一行**：`WorkBuddy 开发对话：https://...`
5. 确认链接在**无登录/隐私窗口**下可打开（公开仓库评审要能看）。

链接 + 文字说明合起来，就是可核验的"对话上下文"。

## 路线 B：手动复制

分享链接不可用时：

1. 在对话流里逐条**复制**用户消息与助手回复（不要改写、不要润色）。
2. 按下面的模板顺序粘贴，保留时间顺序。
3. 至少覆盖主线 8 步（见文末），缺一步就说明导出不完整。

## 路线 C：让我出草稿，你核对定稿

我可以基于本次会话**真实发生的内容**产出结构化草稿，并明确标注
`【原文引用】` / `【摘要】` 两类，不做虚构轮次。
你逐条核对后把定稿覆盖本文件即可。需要的话直接说"生成 workbuddy 草稿"。

---

## 最终文件应有的样子

```markdown
# WorkBuddy 开发对话上下文

- 项目：麦麦权益到期管家（mcd-expiry-butler）
- 客户端：WorkBuddy macOS 桌面版
- 对话时间：2026-10-09 ~ 2026-10-10（北京时间）
- 公开链接：<路线 A 生成的链接>
- 已接入 MCP：mcd-mcp（麦当劳官方，streamableHttp，35 tools）

## 对话记录
### [2026-10-09 17:20] 用户
...（原文粘贴）
### [2026-10-09 17:20] WorkBuddy
...
```

**自检标准：文件里必须有来回多轮的真实问答，不能只是一段总结。**

---

## 公开前脱敏清单（逐项打勾）

- [ ] 搜索 `Bearer`：不应出现真实 Token，替换为 `Bearer <已脱敏>`
- [ ] 搜索券码特征（`MCD` + 字母数字长串）与券 ID（32 位十六进制）：不应出现真实值
- [ ] 搜索 `mcp-approvals`、`~/.workbuddy/mcp.json`：路径中若含 Token 需脱敏
- [ ] 搜索手机号、收货地址、真实姓名：不应出现
- [ ] 搜索 7 位左右纯数字门店编号：替换为 `<门店编号已脱敏>`
- [ ] 搜索 `accountId`、`traceId`：替换为 `<已脱敏>`
- [ ] 确认 `mcp-config.example.json` 中只有 `${MCD_MCP_TOKEN}` 占位符
- [ ] 确认 `demo_output/*.html`、`src/fixtures/*.json` 中无真实券码

一条命令自检（仓库根目录执行）：

```bash
grep -rInE "Bearer [A-Za-z0-9]{12,}|MCD[0-9]{4,}|[A-F0-9]{16,}|1[3-9][0-9]{9}" . --exclude-dir=.git || echo "✅ 未发现疑似凭证"
```

> 注意：这条命令本身包含的模式串**不要**写成真实凭证字面量，否则会把敏感值带进公开仓库。

---

## 本次开发的真实主线（用于核对导出完整性，不是对话记录本身）

1. 检查 WorkBuddy 是否已连接麦当劳 MCP —— 否；官方有远程 MCP（`open.mcd.cn`），需用户自申请 Token
2. 配置 MCP：写 `~/.workbuddy/mcp.json` + 登记信任 `mcp-approvals.json`，重启后连通（35 tools）
3. 抓取活动规则与 `CONTEST_DECLARATION.md`（原样保留，与官方 `diff` 零差异）
4. 真实只读联调：`now-time-info` / `query-nearby-stores` / `query-store-coupons` /
   `query-my-coupons` / `query-my-account` / `mall-points-products` /
   `query-meals` / `query-meal-detail` / `calculate-price`
5. 依据真实返回确定功能边界（详见 `MCP_INTEGRATION.md` 第 5 节）
6. 实现 Skill（`SKILL.md`）+ 核心逻辑（`src/expiry_butler/`）+ 结果页
7. 写 17 个用例并全部通过；生成演示页与真实联调脱敏页
8. 补齐 README / MCP_INTEGRATION / mcp-config.example.json / CONTEST_DECLARATION /
   LICENSE / .gitignore / 演示脚本 / 报名草稿；本机 `git init` 并提交

导出内容若缺其中某步，说明导出不完整，请扩大时间范围重新导出。
