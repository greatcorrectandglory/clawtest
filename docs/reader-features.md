# 文档、阅读功能与留言管理

2026-09-29 已发布到 https://crossthewall.org/ 。本记录补充并更新 `seo-maintenance.md` 的首轮修复结果。

## 已上线的内容

- 测试平台文档中心：17 个目录项均有独立正文页，覆盖开始使用、产品配置、扩展开发、运行维护。内容为公开评估指南，不宣称是特定交付版本的接口手册，也不暴露私有实现。
- 首页、博客列表与项目页：公开说明主站发布曾中断、旧日报暂停，以及恢复测试平台与开发实践更新的方向；撤下固定时间推送承诺。
- 搜索：`/search/`，91 条索引记录，包括文章、站点页面与 17 篇产品文档。无结果与加载失败有明确提示，支持中文输入。
- RSS：导航、页脚、首页更新提示和作者卡片提供入口，订阅地址 `/index.xml`。
- 导航：所有 Hugo 页面使用同一菜单；产品区有返回主站、开发实践、搜索与 RSS 入口。保留原有 `/test-platform/app/index.html` Web UI 演示链接及独立目录。
- 文章页：作者卡片、相关阅读、站内留言。新开发实践文章配置了主题相关的技术文章推荐。
- 五篇测试/欢迎占位文：保留旧地址并设 `noindex`，从文章列表、RSS、搜索和 sitemap 中排除；包括首轮暂留的 `hello-world.md`。
- 主站 sitemap：135 条 URL，包含 22 个产品区页面。产品区独立 sitemap 也包含 17 篇新文档。
- 产品分享图：由现有 SVG 转出 PNG，并补上 Twitter 图片字段。

## 留言审核

服务在本机回环地址 `127.0.0.1:8786` 运行，经 Nginx `/api/comments` 提供同源接口。用户已执行管理员安装命令，公网接口与浏览器提交均已验证。

留言先进入待审队列，不会直接公开。没有面向公网的管理接口，审核通过 SSH 或本机终端完成。

```bash
cd /home/ops/clawd/myblog

# 查看最多 100 条待审留言（包含 id、文章路径、昵称、正文）
python3 scripts/moderate_comments.py list

# 审核通过后才会在文章页展示
python3 scripts/moderate_comments.py approve <留言id>

# 拒绝公开展示
python3 scripts/moderate_comments.py reject <留言id>
```

不应直接批准全部待审留言。先检查是否与文章有关、是否含广告、敏感信息或不适宜公开的内容。拒绝不会删除原始记录，也可撤回已批准留言的公开状态。

## 服务运维

```bash
systemctl --user status crossthewall-comments.service
systemctl --user restart crossthewall-comments.service
journalctl --user -u crossthewall-comments.service --since today
```

- 服务源码：`services/comments/server.py`。
- 用户服务单元：`~/.config/systemd/user/crossthewall-comments.service`，已启用；用户 linger 已开启。
- 私有 SQLite：`~/.local/state/crossthewall-comments/comments.sqlite3`，位于网站目录之外。
- 同目录 `.salt` 文件用于对接入地址作 HMAC；API 不保存明文地址、不公开地址摘要。后续提交时清理超过一天的摘要。
- 默认每个接入地址每小时最多 20 条，限制长度并拒绝短时间重复提交；代理后的访问可能共享此额度。
- 昵称与正文按文本渲染，不能通过留言插入 HTML。跨来源提交、无效文章和占位页提交会被拒绝。
- 本次公网功能验证留言只进入待审队列，确认后已拒绝，没有发布伪造读者留言。批准到公开展示的完整流程在独立测试库中验证。

备份运行中的 SQLite 请使用数据库备份接口，避免只复制主文件而遗漏 WAL：

```bash
python3 - <<'PY'
from pathlib import Path
from datetime import datetime, timezone
import sqlite3
folder = Path.home() / '.local/state/crossthewall-comments'
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
source = sqlite3.connect(folder / 'comments.sqlite3')
target = sqlite3.connect(folder / f'comments-backup-{stamp}.sqlite3')
source.backup(target)
target.close()
source.close()
PY
```

## 发布与验证

主站继续使用 `python3 scripts/deploy_site.py --apply`。新增 `search/`、`updates/`、`index.json` 和 Hugo 输出的 `js/` 到发布范围；验证同时覆盖 SEO 和阅读功能。检查所有模板引用的本地脚本文件，避免生成页存在而功能脚本漏发。

产品区源码在 `/home/ops/work/test_platform_gui/greatcorrectandglory.github.io`，与博客分开构建；其新增文档数据同步到博客的 `data/product_docs.json`（用于全站搜索）及 `data/standalone_pages.toml`（用于主站 sitemap）。修改产品文档后需要同步两处并重建两站。

```bash
python3 -m unittest discover -s tests -v
python3 scripts/check_seo.py /var/www/crossthewall.org
python3 scripts/check_reader_features.py /var/www/crossthewall.org
```

本轮结果：

- 10 个 Python 测试通过：审核状态隔离、跨源与无效文章拒绝、重复/过长/限流、发布保护与回滚、日报时效性保护。
- 产品站 `npm test` 与 `npm run build` 通过，生成 22 个页面。
- 主站构建及发布后检查：138 个模板页、135 个 sitemap URL、91 条搜索索引。
- 备用站构建检查通过，未推送或发布备用镜像。
- 公网逐一检查 135 个 sitemap 地址全部 HTTP 200；中文标记与描述有效；随机不存在路径返回真实 404 和 `noindex`。
- 桌面与移动端 10 个页面场景通过浏览器检查，无横向溢出；搜索、手机菜单、作者/相关阅读和留言提交经过交互验证。
- 本地完整留言流程验证提交、待审隐藏、审批后公开及 HTML 按文本显示；公网实际提交进入私有队列且未公开，验证后拒绝。

证据在 `/home/ops/work/test_platform_gui/artifacts/20260929-public-site/`。
完整发布前备份在 `/home/ops/backups/crossthewall/20260929-content-ux/`。
博客发布归档：`~/.local/state/crossthewall-deployments/20260929T061438.390187Z/`；补发脚本归档：`20260929T061750.536734Z/`。
产品区 26 个文件的改动与回退备份在完整备份目录下的 `product-release/`，没有删除独立 Web UI。
