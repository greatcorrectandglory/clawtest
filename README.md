# clawtest

这是一个 **Hugo + PaperMod** 的静态博客站点源码仓库。

- Cloudflare Pages（主站）：从 GitHub 自动拉取构建发布
- GitHub Pages（备用镜像）：通过 GitHub Actions 自动构建发布

---

## 本地预览

```bash
# 进入仓库
cd myblog

# 本地预览（开发模式）
hugo server -D
```

构建静态文件：

```bash
hugo
# 输出目录：./public
```

> 说明：之前在 Cloudflare 上使用 `hugo --minify` 可能会触发主题/页面的 JSON minify 解析错误；
> 如果遇到构建失败，先用纯 `hugo` 跑通。

---

## Cloudflare Pages 部署（自动更新）

在 Cloudflare Pages 里使用 **Connect to Git** 绑定本仓库：

- Build command：`hugo`
- Build output directory：`public`
-（可选）环境变量：
  - `HUGO_VERSION=0.146.5`
  - `HUGO_ENV=production`

之后每次 `git push` 到 `main`，Cloudflare Pages 会自动构建并发布。

---

## GitHub Pages 部署（自动更新）

本仓库已内置 GitHub Actions 工作流：`.github/workflows/pages.yml`。

启用方式：

1. 打开 GitHub 仓库 → **Settings** → **Pages**
2. Source 选择 **GitHub Actions**
3. 之后每次 push 到 `main`，Actions 会自动构建并发布

GitHub Pages 默认地址一般是：

- `https://greatcorrectandglory.github.io/clawtest/`

> 注意：GitHub Pages 是子路径发布（`/clawtest/`）。
> 为了保证链接正确，本工作流在构建时会强制设置 baseURL。

---

## 写作与发布

新增文章一般放在：

- `content/posts/`

写完推送即可触发 Cloudflare Pages / GitHub Pages 自动更新：

```bash
git add .
git commit -m "new post"
git push
```
