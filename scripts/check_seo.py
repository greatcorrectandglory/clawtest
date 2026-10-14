#!/usr/bin/env python3
"""Validate a production Hugo build without network or third-party dependencies."""
import argparse
import json
import tomllib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
import xml.etree.ElementTree as ET


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.lang = ""
        self.meta = {}
        self.canonical = ""
        self.navigation = []
        self.scripts = []
        self.icons = []
        self.in_menu = False
        self.json_blocks = []
        self.in_json = False
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.lang = attrs.get("lang", "")
        if tag == "meta":
            key = attrs.get("name", attrs.get("property", attrs.get("http-equiv", "")))
            self.meta.setdefault(key, []).append(attrs.get("content", ""))
        if tag == "link" and "icon" in attrs.get("rel", ""):
            self.icons.append(attrs.get("href", ""))
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href", "")
        if tag == "ul" and attrs.get("id") == "menu":
            self.in_menu = True
        if tag == "a" and self.in_menu:
            self.navigation.append(attrs.get("href", ""))
        if tag == "script" and attrs.get("src"):
            self.scripts.append(attrs["src"])
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self.in_json = True
            self.json_blocks.append("")

    def handle_endtag(self, tag):
        if tag == "ul":
            self.in_menu = False
        if tag == "script":
            self.in_json = False

    def handle_data(self, data):
        if self.in_json:
            self.json_blocks[-1] += data


def check(destination, base_url):
    failures = []

    def require(condition, message):
        if not condition:
            failures.append(message)

    home = Page(destination / "index.html")
    pages = [destination / "index.html", destination / "404.html"]
    for section in ("posts", "about", "projects", "tags", "categories", "search", "updates"):
        pages.extend((destination / section).rglob("*.html"))
    checked = 0
    for path in pages:
        page = Page(path)
        # Hugo pagination aliases contain only redirects, not the site template.
        if "refresh" in page.meta:
            continue
        checked += 1
        label = str(path.relative_to(destination))
        require(page.lang.lower() == "zh-cn", f"{label}: language must be zh-cn")
        descriptions = []
        for key in ("description", "og:description", "twitter:description"):
            values = page.meta.get(key, [])
            require(len(values) == 1, f"{label}: expected one {key}")
            value = values[0] if values else ""
            require(0 < len(value) <= 160, f"{label}: {key} length {len(value)}")
            descriptions.append(value)
        require(len(set(descriptions)) == 1, f"{label}: descriptions disagree")
        for key in ("og:image", "twitter:image"):
            images = page.meta.get(key, [])
            require(bool(images), f"{label}: missing {key}")
            for url in images:
                require(url.startswith("https://"), f"{label}: image must be absolute HTTPS")
                if url.startswith(base_url):
                    image = destination / unquote(url[len(base_url):])
                    require(image.is_file(), f"{label}: missing image {image}")
        require(page.canonical.startswith(base_url), f"{label}: wrong canonical")
        if "/page/" in label:
            expected = base_url + label.removesuffix("index.html")
            require(unquote(page.canonical) == expected, f"{label}: paginated canonical must be self-referencing")
        for script in page.scripts:
            url = urljoin(page.canonical, script)
            if url.startswith(base_url):
                resource = destination / unquote(urlsplit(url[len(base_url):]).path)
                require(resource.is_file(), f"{label}: missing script {resource}")
        require(page.navigation == home.navigation, f"{label}: inconsistent main navigation")
        require(bool(page.icons), f"{label}: missing site icon")
        for icon in page.icons:
            if icon.startswith(base_url):
                require((destination / unquote(icon[len(base_url):])).is_file(), f"{label}: missing icon {icon}")
        nodes = []
        for block in page.json_blocks:
            try:
                data = json.loads(block)
                nodes.extend(data.get("@graph", [data]))
            except ValueError as error:
                failures.append(f"{label}: invalid JSON-LD: {error}")
        types = [node.get("@type") for node in nodes]
        indexable = "noindex" not in page.meta.get("robots", [""])[0]
        if indexable:
            require("WebSite" in types and "Person" in types, f"{label}: missing site/author identity")
            is_post = label.startswith("posts/") and "/page/" not in label and label != "posts/index.html"
            require(("BlogPosting" in types) == is_post, f"{label}: wrong article classification")
        for node in nodes:
            if node.get("@type") == "BreadcrumbList":
                crumbs = node.get("itemListElement", [])
                require(len(crumbs) >= 2, f"{label}: breadcrumb needs home and page")
                require([c.get("position") for c in crumbs] == list(range(1, len(crumbs) + 1)), f"{label}: non-consecutive breadcrumbs")
                require(crumbs[0].get("item") == base_url, f"{label}: breadcrumb must begin at home")
            if node.get("@type") == "BlogPosting":
                require(node.get("datePublished") and node.get("dateModified"), f"{label}: missing article dates")
                image_url = node.get("image", "")
                if image_url.startswith(base_url):
                    require((destination / unquote(image_url[len(base_url):])).is_file(), f"{label}: missing article image {image_url}")
    require("noindex" in Page(destination / "404.html").meta.get("robots", [""])[0],
            "404 must be noindex")
    require("noindex" not in home.meta.get("robots", [""])[0], "home must be indexable")
    require(any(url.endswith("test-platform/") for url in home.navigation), "missing product navigation")
    require(any(url.endswith("work/") for url in home.navigation), "missing work navigation")
    about = (destination / "about/index.html").read_text()
    require('href="mailto:"' not in about, "empty email link")
    require('href="https://github.com/"' not in about, "empty GitHub link")
    require('href="https://github.com/greatcorrectandglory"' in about, "missing GitHub profile")

    urls = [node.text for node in ET.parse(destination / "sitemap.xml").findall(".//{*}loc")]
    require(len(urls) == len(set(urls)), "duplicate sitemap URLs")
    require(base_url + "work/" in urls, "work absent from sitemap")
    product_paths = tomllib.loads((Path(__file__).resolve().parents[1] / "data/standalone_pages.toml").read_text())["paths"]
    for path in product_paths:
        require((base_url + path in urls) == (base_url == "https://crossthewall.org/"),
                f"wrong standalone sitemap entry: {path}")
    for url in urls:
        require(url.startswith(base_url), f"foreign sitemap URL: {url}")
        path = unquote(url[len(base_url):])
        if not path.startswith("test-platform/"):
            page_path = destination / path / "index.html"
            require(page_path.is_file(), f"missing sitemap target: {path}")
            if page_path.is_file():
                require("noindex" not in Page(page_path).meta.get("robots", [""])[0],
                        f"noindex target in sitemap: {path}")
    require(not any("404.html" in url for url in urls), "404 in sitemap")
    for slug in ("测试", "测试自动化", "推特测试", "测试文章-hello-world", "hello-world"):
        url = base_url + "posts/" + slug + "/"
        require(url not in [unquote(value) for value in urls], f"placeholder in sitemap: {slug}")
        placeholder = Page(destination / "posts" / slug / "index.html")
        require("noindex" in placeholder.meta.get("robots", [""])[0], f"indexable placeholder: {slug}")
        for rss in (destination / "index.xml", destination / "posts/index.xml"):
            links = [node.text for node in ET.parse(rss).findall(".//item/link")]
            require(url not in [unquote(value) for value in links], f"placeholder in RSS: {slug}")
        for listing in (destination / "posts").glob("**/index.html"):
            if listing.parent == destination / "posts" or "page" in listing.relative_to(destination / "posts").parts:
                require(url not in unquote(listing.read_text()), f"placeholder in listing: {slug}")
    work = Page(destination / "work/index.html")
    require(work.lang.lower() == "zh-cn", "work language")
    for key in ("description", "og:description", "twitter:description", "og:image", "twitter:image"):
        require(bool(work.meta.get(key, [""])[0]), f"work missing {key}")
    require(work.canonical == "https://crossthewall.org/work/", "work canonical")
    if failures:
        raise SystemExit("SEO validation failed:\n" + "\n".join(failures))
    print(f"SEO validation passed: {checked} templated pages, {len(urls)} sitemap URLs; {base_url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--base-url", default="https://crossthewall.org/")
    args = parser.parse_args()
    check(args.destination, args.base_url.rstrip("/") + "/")
