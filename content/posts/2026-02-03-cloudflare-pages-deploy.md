+++
title = "把 Hugo 博客部署到 Cloudflare Pages（GitHub 自动更新版）"
date = 2026-02-03T16:17:00+08:00
tags = ["AI", "Blog", "Cloudflare"]
categories = ["AI"]
draft = false
+++

这篇文章记录我把本地（或 VPS 上）的 **Hugo 静态博客**迁移到 **Cloudflare Pages** 的全过程，并实现：

- **GitHub 仓库驱动发布**：每次 `git push` 都会触发自动构建与部署
- **pages.dev 域名直接上线**（也支持后续绑定自定义域名）

> 我的目标很简单：以后只管写文章 + push，其它交给 Cloudflare。

---

## 0. 你需要准备什么

- 一个 Hugo 站点（例如本地 `myblog/`）
- 一个 GitHub 仓库（用于存放站点源码）
- 一个 Cloudflare 账号

---

## 1. 把 Hugo 站点推到 GitHub

进入 Hugo 目录：

```bash
cd ~/clawd/myblog
```

初始化仓库并写 `.gitignore`（不要把构建产物提交上去）：

```bash
git init

cat > .gitignore <<'EOF'
public/
resources/
.hugo_build.lock
.DS_Store
EOF
```

提交代码：

```bash
git add .
git commit -m "init blog"
```

绑定远端并推送（仓库名以你的为准）：

```bash
git remote add origin git@github.com:greatcorrectandglory/clawtest.git
git branch -M main
git push -u origin main
```

> 如果你还没配置 SSH key，需要先把服务器的 `~/.ssh/id_ed25519.pub` 添加到 GitHub 的 SSH keys。

---

## 2. Cloudflare Pages 连接 GitHub（关键步骤）

在 Cloudflare Dashboard：

1. 进入 **Pages**
2. 点击 **Create a project**
3. 选择 **Connect to Git**
4. 选择 GitHub 并授权
5. 选择仓库：`greatcorrectandglory/clawtest`
6. 选择分支：`main`

### 构建配置（Hugo）

- **Build command**：
  ```
  hugo
  ```
  
  > 注意：我最初用了 `hugo --minify`，在某些主题/页面上可能会触发 minify 的 JSON 解析错误；如果你遇到类似报错，先用纯 `hugo` 跑通再说。

- **Build output directory**：
  ```
  public
  ```

- （可选）环境变量：
  - `HUGO_VERSION = 0.146.5`
  - `HUGO_ENV = production`

保存后，Cloudflare 会立刻开始第一次构建，成功后会给你一个地址：

- `https://xxx.pages.dev`

---

## 3. 配置 baseURL（建议）

为了让站内链接、RSS、分享链接更规范，建议在 `hugo.toml` 里设置：

```toml
baseURL = "https://你的项目.pages.dev/"
relativeURLs = false
```

修改后提交并 push：

```bash
git add hugo.toml
git commit -m "set baseURL for Cloudflare Pages"
git push
```

---

## 4. 自动更新怎么工作？

当 Pages 连接 GitHub 后，流程是：

1. 你写文章（新增/修改 `content/posts/*.md`）
2. 执行：
   ```bash
   git add .
   git commit -m "new post"
   git push
   ```
3. Cloudflare Pages 自动：
   - 拉取最新代码
   - 执行 `hugo` 构建
   - 发布到 `pages.dev`

你可以在 Cloudflare Pages 的 **Deployments** 页面看到每次部署记录。

---

## 5. 验证“确实会自动更新”（一分钟测试）

你可以做一个最小改动，比如在这篇文章末尾加一行文本，然后：

```bash
git add .
git commit -m "test auto deploy"
git push
```

接着打开 Cloudflare 的 Deployments，你应该能看到一条新的构建任务，然后网页内容会更新。

---

## 6. 后续：自定义域名（可选）

Pages 支持绑定自定义域名（例如 `blog.example.com`），并自动处理 HTTPS。
等域名准备好后，把 `baseURL` 改成你的自定义域名即可。

---

到这里，Hugo 博客的 Cloudflare Pages（GitHub 自动更新版）就完成了：写作 → push → 自动发布。
