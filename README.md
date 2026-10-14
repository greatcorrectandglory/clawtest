# clawtest

这是一个 **Hugo + PaperMod** 的静态博客站点源码仓库。

- 当前主站：`https://crossthewall.org/`，由本机 Nginx 从 `/var/www/crossthewall.org` 提供页面。
- GitHub Pages（备用镜像）：通过 GitHub Actions 自动构建发布。
- Cloudflare Pages：历史发布目标，向它推送不等于更新当前 Nginx 主站。

部署现状、SEO 修复及验证步骤见 [SEO 维护说明](docs/seo-maintenance.md)。最新文档、搜索、RSS 与评论功能，以及审核命令见 [阅读功能与留言管理](docs/reader-features.md)。

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

## Cloudflare Pages 部署（历史配置）

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

## 写作与主站发布

新增文章放在 `content/posts/`，保持 `draft = true` 至审稿完成，并填写 `description`。内容方向为「测试平台与开发实践」，选题见 [内容计划](docs/editorial-plan.md)。

```bash
# 生成草稿
/home/ops/.local/bin/hugo new posts/my-post.md

# 验证发布保护
python3 -m unittest discover -s tests -v

# 构建并查看发布计划，不改线上
python3 scripts/deploy_site.py

# 审稿和构建检查完成后，发布到实际 Nginx 主站
python3 scripts/deploy_site.py --apply
```

旧入口 `/home/ops/clawd/scripts/deploy-blog.sh` 已转发到此流程；`DRY_RUN=1` 只构建和检查。每次发布保存变更清单与备份，发布验证失败会自动回滚，独立应用和 OTA 目录不受影响。

Git 提交与推送单独进行，不是主站发布的前提；推送到 `main` 仍会触发已配置的 GitHub Pages 镜像工作流。暂存文件前请检查 `git diff`，不要混入其他任务的改动。
