# 把演示页发布到 GitHub Pages（约 5 分钟）

目标：得到一个公开链接 `https://baihua2471.github.io/mcd-expiry-butler/`，
填进仓库 About 的 **Website**，让访客不装任何东西就能看懂项目。

页面内容 = 项目简介 + 演示模式结果页（样例数据），不含任何真实账户信息。

---

## 前提

代码已推送到 GitHub（见 `GITHUB_SETUP.md` 第 1、2 步），且 `docs/index.html` 已提交。

## 步骤

1. 打开仓库 → **Settings** → 左侧 **Pages**
2. **Build and deployment** 区域：
   - Source：`Deploy from a branch`
   - Branch：`main`，Folder：**`/docs`** ← 一定要选 docs，不是 root
   - 点 **Save**
3. 等待 1~2 分钟，页面顶部会出现绿色提示：
   `Your site is live at https://baihua2471.github.io/mcd-expiry-butler/`
4. 点开确认能访问（首次部署偶尔要等 5 分钟）。

## 填进 About

仓库首页右侧 About 区 → 齿轮 ⚙️ →
**Website** 填 `https://baihua2471.github.io/mcd-expiry-butler/` → Save

## 以后更新演示页

改了数据或样式后重新生成并推送即可：

```bash
cd /Users/wangkui/WorkBuddy/2026-10-09-17-20-07/mcd-expiry-butler
python3 scripts/build_pages.py        # 重新生成 docs/index.html
git add docs/index.html && git commit -m "pages: 更新演示页" && git push
```

Pages 会在推送后自动重新部署（约 1 分钟生效，浏览器缓存可能要强刷 Cmd+Shift+R）。

## 常见问题

| 现象 | 原因与处理 |
|---|---|
| 404 | 多数是 Folder 选成了 root；回 Settings → Pages 改成 `/docs` 再 Save |
| 样式丢了 | `docs/index.html` 是单文件自包含 HTML，不存在丢外部资源的问题；若 404 见上一条 |
| 改了没生效 | 部署排队中或浏览器缓存，等 1 分钟强刷 |
| 想自定义域名 | Settings → Pages → Custom domain（可选，不做也完全不影响参赛） |
