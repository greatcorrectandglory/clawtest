# Hugo 网站维护

- 源码：Hugo 0.146.5 + vendored PaperMod；文章在 `content/`，静态资源在 `static/`，站点级模板覆盖在 `layouts/`。
- 修改前检查 Git 状态，保留用户已有修改。不要直接修改 vendored 主题来实现站点定制。
- 主站实际由本机 Nginx 的 `/var/www/crossthewall.org` 提供；GitHub/Cloudflare Pages 是独立发布目标。
- 在新建的临时目录构建，避免把旧产物混入验证。运行 `hugo --environment production --destination "$BUILD_DIR"`，再运行 `python3 scripts/check_seo.py "$BUILD_DIR"`。
- 同时验证 GitHub Pages 子路径：构建时传 `--baseURL https://greatcorrectandglory.github.io/clawtest/`，检查脚本传同值 `--base-url`。
- 不提交 `public/`、`resources/`、工具下载和临时构建目录。
- `layouts/partials/head.html` 和 `layouts/partials/templates/` 覆盖主题 SEO 实现；主题升级后须对照上游变化并重新验证。
- `test-platform/` 独立部署；其 sitemap 入口维护在 `data/standalone_pages.toml`。生产根目录还包含其他独立服务，不能用博客构建结果清空整个根目录。
- 发布流程及已知内容问题见 `docs/seo-maintenance.md`。不要通过改日期制造更新，也不要自动恢复资讯发布任务。

## 发布与内容

- 主站用 `python3 scripts/deploy_site.py --apply` 发布；不带 `--apply` 时仅构建、验证并输出计划。旧外部入口已转发到仓库版本。
- 发布脚本变更运行 `python3 -m unittest discover -s tests -v`，必须保留独立目录保护与失败回滚。
- 用户确认内容方向为「测试平台与开发实践」。选题与事实验证要求见 `docs/editorial-plan.md`。
- 不将 `docs/held-digests.json` 中过时日报自动转为发布状态。日报导入必须通过 `scripts/import_digest.py`，只生成草稿。

- 站内留言为先审后公开，服务与数据库在网站目录之外；不要将测试留言批准到生产公开列表。操作见 `docs/reader-features.md`。
- 文档内容在产品站 `src/data/documentation.json`，更新后同步博客 `data/product_docs.json` 与 `data/standalone_pages.toml`，并分别验证两站。
- `scripts/check_reader_features.py` 验证搜索/RSS/推荐及占位文排除；SEO 检查还会验证页面引用的本地脚本是否已发布。
