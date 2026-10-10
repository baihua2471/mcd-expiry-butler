# 在 GitHub 上创建 mcd-expiry-butler 仓库

本机的 Git 部分已经准备好（3 个 commit，26 个文件）。
下面从"建仓库"到"能拿到 Star"走一遍。

---

## 第 1 步：建空仓库（网页）

1. 登录 GitHub → 右上角 `+` → **New repository**
2. 填写：

   | 字段 | 值 |
   |---|---|
   | Owner | 你的账号（当前 SSH 指向 **baihua2471**） |
   | Repository name | `mcd-expiry-butler` |
   | Description | `看看哪些麦当劳权益快到期，哪些值得用，哪些不用为了到期硬消费。` |
   | 可见性 | **Public**（规则要求公开可访问，私有不计入排名） |

3. **全部不要勾**：Add a README file / Add .gitignore / Choose a license —— 都不要选。
   本机已经有这些文件，选了会导致首次 push 冲突。
4. 点 **Create repository**。
5. 在接下来的页面复制 **SSH** 地址：`git@github.com:<你的账号>/mcd-expiry-butler.git`

> SSH 已验证可用：`ssh -T git@github.com` 返回 `Hi baihua2471! You've successfully authenticated`。
> （顺带修了个坑：你的 22 端口在握手阶段超时，已把 `~/.ssh/config` 里的 github.com 改走
> `ssh.github.com:443`，原配置备份在 `~/.ssh/config.bak.*`。）

## 第 2 步：推送

```bash
cd /Users/wangkui/WorkBuddy/2026-10-09-17-20-07/mcd-expiry-butler
git remote add origin git@github.com:<你的账号>/mcd-expiry-butler.git
git branch -M main
git push -u origin main
```

推完刷新页面确认能看到 README 渲染，且 `demo_output/` 里的图片正常显示。

## 第 3 步：加话题标签（提升被搜到）

仓库页右侧齿轮 → **Topics**，建议：

```
mcp    model-context-protocol    workbuddy    mcdonalds
skill    ai-agent    coupon-reminder    python
```

## 第 4 步：核对规则硬指标

- [ ] 仓库 **Public**
- [ ] 根目录五个必交文件齐全：`README.md` `CONTEST_DECLARATION.md`
      `MCP_INTEGRATION.md` `mcp-config.example.json` `workbuddy.md`
- [ ] `workbuddy.md` 是真实对话上下文（不是占位说明）
- [ ] 创建时间在 2025-12-25 ~ 2026-10-25 之间

## 第 5 步：提交报名 Issue

- 目标仓库：https://github.com/M-China/mcd-developer-innovation-challenge
- 用活动页提供的 **Issue 模板**提交
- 内容草稿：`docs/SUBMISSION_ISSUE.md`（把项目地址占位符换成真实地址）
- **截止 2026-10-25 23:59**，Star 统计截止 2026-10-26 00:00（北京时间）

> 规则提示：同一 GitHub 账号下只有 Star 数最高的项目进排行榜，
> 所以这个号如果还有别的项目参赛，精力集中在这一个上。

---

## 常用后续命令

```bash
# 改完文件后提交
git add -A && git commit -m "docs: ..." && git push

# 查看推送地址
git remote -v

# 万一 push 报冲突（建仓时误勾了 README）
git pull --rebase origin main && git push
```
