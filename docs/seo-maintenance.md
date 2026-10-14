# SEO 修复与发布记录

首轮完成日期：2026-09-29。以下为首轮修复记录。随后新增的 17 篇文档、搜索、RSS、作者卡片与留言服务，以及当前页面统计，见 [阅读功能与留言管理](reader-features.md)。

## 修复结果

| 问题 | 已完成的处理 |
| --- | --- |
| 首页缺少描述 | 增加站点简介，并为博客列表、项目和关于页提供独立摘要 |
| HTML 语言错误 | 默认语言改为 `zh-cn`，启用中文摘要处理；独立应用原有中文标记保留 |
| sitemap 漏页 | 增加工作页和独立测试平台的五个公开页面 |
| 404 允许收录 | 模板强制 `noindex`；随机不存在路径实际返回 HTTP 404 |
| 分享信息不完整 | 配置 PNG 默认头像、OG/Twitter 描述，保留文章封面优先规则；工作页补 canonical 与分享标签 |
| 文章描述过长 | 搜索、分享及文章 JSON-LD 共用纯文本摘要，站点约定上限 160 个 Unicode 字符 |
| 导航不一致 | 整站从相同配置重建 Hugo 导航；独立页面保留各自的页内导航 |
| 占位测试文章 | 四篇原 URL 继续可访问，设置 `noindex`，排除文章列表、RSS 和 sitemap |
| GitHub 与邮箱空链接 | GitHub 指向真实账号，移除未配置的邮箱入口 |
| 博客停更 | 发布「测试平台开发实践：让一次测试结果能够被复现」，日期为真实发布日期；修复主站发布链路 |

## 停更原因与内容处理

旧博客主站仅有到 2026-04-13 的构建，但源码包含至 6 月的文章。旧发布脚本推送 GitHub/Cloudflare Pages，只把 `static/` 应用复制到本机，没有构建和同步本机 Nginx 的文章页面。

新增的 25 篇 5—6 月日报也不能直接上线：来源日期明显早于文章日期，最新一篇引用的资料仍停留在 3 月。这些文件已设置 `draft = true`，原文和日期完整保留，清单见 `held-digests.json`。

旧 `knowledge-flow-digest.service` 指向已不存在的 `/opt/knowledge-flow`，现有 timer 仍会尝试启动并失败。另有旧 OpenClaw 日报任务记录了认证与限流错误。此次没有重建这些旧的自动内容服务、启动它们或发送 Telegram/微信消息。按用户确认，内容方向改为测试平台与开发实践，选题与质量要求见 `editorial-plan.md`；目前采用审稿后发布，不承诺自动持续更新。

## 当前部署结构

- 源码：`/home/ops/clawd/myblog`，Git 远端为 `git@github.com:greatcorrectandglory/clawtest.git`。
- 主站：本机 Nginx，根目录 `/var/www/crossthewall.org`。
- GitHub Pages：独立备用镜像；通过既有工作流发布。本次只验证了镜像构建，没有推送或发布镜像。
- `test-platform/`、`ota/`、`muyu/`、`freefall-sphere/`：独立目录，博客发布不覆盖它们。

## 发布与回滚

Hugo 0.146.5 位于 `/home/ops/.local/bin/hugo`，下载时已对照官方 checksums 校验。

```bash
cd /home/ops/clawd/myblog

# 构建、检查并显示计划，不修改线上目录
python3 scripts/deploy_site.py

# 构建检查通过后发布，发布后再检查；失败自动恢复受影响文件
python3 scripts/deploy_site.py --apply

# 旧调用入口已转发到同一流程
/home/ops/clawd/scripts/deploy-blog.sh
```

发布只写入 Hugo 所属目录及少量根文件；只有 `posts/`、`tags/`、`categories/`、`about/`、`projects/` 可清理本次构建中已不存在的旧产物。独立应用与服务目录不参与同步。每次构建、变更清单和文件备份存入 `~/.local/state/crossthewall-deployments/`，默认权限仅当前用户可访问。每个文件通过临时文件替换，发布异常会恢复改动、删除和新增文件。发布脚本不再自动提交整个工作区、推送 Git 或发送消息。

本次完整站点与源码备份：`/home/ops/backups/crossthewall/20260929-before-seo/`。

本次发布归档：`/home/ops/.local/state/crossthewall-deployments/20260929T054529.877266Z/`，包含 `plan.json`、`rollback.json`、`previous/`、`build/` 和公网检查记录 `http-checks/results.json`。

## 验证结果

- 发布脚本与日报导入的 6 个测试通过，包括独立应用保护、失败回滚、符号链接越界、旧来源/未来日期拒绝与草稿生成。
- 主站构建及部署后的文件检查通过：136 个模板页面，118 条 sitemap URL。
- GitHub Pages 子路径构建检查通过：136 个模板页面，113 条 sitemap URL；不声明没有部署的独立产品路径。
- 公网逐一请求 118 个 sitemap 地址：全部 HTTP 200，语言为中文、有描述且没有误加 `noindex`。
- 公网随机不存在路径及源站 HTTPS 回环请求：HTTP 404，页面带 `noindex`。
- 公网测试占位文章：保留 HTTP 200，但带 `noindex`；不出现在 sitemap。
- 公网 robots.txt 与 PNG 分享图：HTTP 200。
- 4 个独立应用/服务目录的 31 个文件：与发布前备份相比，SHA-256 全部一致。
- 本次发布写入 212 个文件，无删除文件；`git diff --check` 通过。

复查命令：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_seo.py /var/www/crossthewall.org
```

## AI 日报归档（2026-10-14）

已发布的 63 篇 2—4 月日报及 1 篇发布链路测试文章（GLM-5 等近况速览）移入 `content/posts/ai-digest/`，每篇用 `url` 保留原地址 `/posts/<文件名>/`。归档目录的 `_index.md` 通过 cascade 设置 `robotsNoIndex`、`archived`、`build.list = "local"` 和 `sitemap.disable`：日报只在 `/posts/ai-digest/` 列出，不进入博客列表、首页、RSS、搜索、标签页和 sitemap，单页顶部显示归档提示。日报的 tags/categories 已移除，原先只含日报的标签页及多余分页不再生成。

`import_digest.py` 仍向 `content/posts/` 写草稿；如要把新日报放进归档，需手动移到 `ai-digest/` 并补 `url`。

## 日报导入保护

仓库的 `scripts/import_digest.py` 检查每一条资料的发布日期和来源链接；任何一条超出指定日期的近七天窗口、日期缺失或在未来，都会拒绝导入。校验通过也只生成 `draft = true` 的草稿，不覆盖已有不同内容的文章。`--dry-run` 不写文件。外部旧 `sync-digest-to-blog.sh` 已转发到此实现。

## 搜索表现的解释边界

技术修复已在公网生效，搜索引擎仍需重新抓取。meta description 可以帮助提供摘要，但不能保证搜索引擎采用指定文字；停更天数本身也不能简单等同于排名损失。持续更新应提供真实、有用的内容。

参考：
- https://developers.google.com/search/docs/appearance/snippet
- https://developers.google.com/search/docs/fundamentals/creating-helpful-content
