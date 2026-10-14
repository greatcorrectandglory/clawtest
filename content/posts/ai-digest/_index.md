+++
title = "AI 日报归档"
date = 2026-04-13T08:00:00+08:00
description = "2026 年 2—4 月自动整理的 AI 技术日报，已停止更新，仅作存档。资讯可能已过时，请以原始来源为准。"
robotsNoIndex = true
weight = 100
outputs = ["html"]

[sitemap]
  disable = true

# 日报只在本归档页列出：不进入博客列表、首页、RSS、站内搜索、标签页和相关推荐
[[cascade]]
  robotsNoIndex = true
  archived = true
  [cascade.build]
    list = "local"
  [cascade.sitemap]
    disable = true
+++

当前博客聚焦测试平台与开发实践，[返回博客](../)。
