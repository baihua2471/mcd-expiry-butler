# 发布到 GitHub 前的自检清单

> 仓库已在本机完成 `git init` 与首次提交（commit `ef74828`，26 个文件）。
> 本清单用于推送**之前**最后确认，尤其是第 1 项（会直接影响 WorkBuddy 专项奖励资格）。

## 一、必办（阻塞发布）

- [ ] **替换 `workbuddy.md`**：当前内容是占位说明，不是真实对话上下文。
      必须由你在 WorkBuddy 客户端导出本次开发对话为 Markdown，**覆盖**该文件。
      用总结冒充会被认定为虚假材料；请勿让我代写。
- [ ] 导出后执行脱敏自检（见下第三节），确认全文无 Token / 券码 / 门店编号 / 手机号。
- [ ] 确认 GitHub 仓库**公开可访问**（规则要求项目须发布至公开可访问的个人仓库，私有仓库不计入排名）。

## 二、规则合规（已核对 activityGuidelines.md）

| 规则要求 | 状态 |
|---|---|
| README.md：介绍 / 安装 / 使用示例 / 目标用户 | ✅ 齐备，另含演示模式、限制、免责 |
| CONTEST_DECLARATION.md：原样取用 | ✅ 与官方 raw 文件 `diff` 一致（1522 字节，零差异） |
| MCP_INTEGRATION.md：实际工具 / 流程 / 价值 / 联调状态 | ✅ 已写，含未验证项清单 |
| mcp-config.example.json：仅环境变量占位符 | ✅ `${MCD_MCP_TOKEN}`，无真实凭证 |
| workbuddy.md（WorkBuddy 专项） | ⚠️ **待你导出替换** |
| 仓库创建时间在 2025-12-25 ~ 2026-10-25 | ✅ 在窗口内 |
| 真实使用麦当劳 MCP | ✅ 10 个只读工具实调，快照存于 `src/fixtures/real_case_sanitized.json` |
| 内容合规：无品牌素材 / 不诋毁 / 不诱导过度消费 | ✅ 原创页面设计，无 Logo；业务原则明确「预算优先、不鼓励凑单」 |

未列入规则但建议：**LICENSE** 已补充（MIT），便于他人合规使用与传播。

## 三、脱敏自检命令（推送前必跑）

```bash
cd mcd-expiry-butler
# 1) 已知敏感串
grep -rInE "Bearer [A-Za-z0-9]{6,}|1i59h7|MCD[0-9]{4,}|71F939|E86377|1420762|1[0-9]{10}" . || echo "✅ 无命中"
# 2) 检查 git 历史里是否曾带入敏感文件
git log --all --full-history --name-only | sort -u | grep -iE "\.env|token|secret|address" || echo "✅ 历史干净"
```

## 四、推送命令（在 GitHub 建好空仓库后执行，不要勾选README/LICENSE初始化）

```bash
cd /Users/wangkui/WorkBuddy/2026-10-09-17-20-07/mcd-expiry-butler
git remote add origin git@github.com:<你的账号>/mcd-expiry-butler.git
git branch -M main
git push -u origin main
```

## 五、发布后

- 报名截止 **2026-10-25 23:59**，Star 统计截止 **2026-10-26 00:00**（北京时间）。
- 用 Issue 模板提交报名，内容草稿在 `docs/SUBMISSION_ISSUE.md`。
- 规则限制：同一 GitHub 账号仅 Star 数最高的项目进榜。
