#!/usr/bin/env python3
"""Checks the built site in _site/ for the things this site is supposed to have.

Run after `bundle exec jekyll build`:

    python3 scripts/test_site.py

Exits non-zero and prints one line per failure. Stdlib only, no test framework.
"""

import html
import os
import re
import sys
from urllib.parse import unquote, urljoin, urlparse

SITE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_site")

# Nav order comes from _data/navigation.yml. Header link 0 is the site title.
EXPECTED_NAV = ["Home", "Research", "Projects", "Experience", "CV", "Contact"]

# permalink -> text that must appear in the rendered page body
EXPECTED_PAGES = {
    "/": "Research interests",
    "/research/": "Supply-Chain Risk &amp; Financial Markets",
    "/projects/": "Technical skills",
    "/experience/": "Reframe Innovations, Inc.",
    "/cv/": "bryan-zin-cv.pdf",
    "/contact/": "bz297@cornell.edu",
}

# permalink -> exact <title> text. The home page's page.title equals site.title,
# so it must render the name once, not "Bryan Zin Bryan Zin".
EXPECTED_TITLES = {
    "/": "Bryan Zin",
    "/research/": "Research Bryan Zin",
    "/projects/": "Projects Bryan Zin",
    "/experience/": "Experience Bryan Zin",
    "/cv/": "CV Bryan Zin",
    "/contact/": "Contact Bryan Zin",
}

# Template pages that were removed; none of these should still be published.
REMOVED_ROUTES = [
    "/publications/",
    "/talks/",
    "/teaching/",
    "/portfolio/",
    "/markdown/",
    "/terms/",
    "/cv-json/",
    "/talkmap/",
    "/year-archive/",
    "/category-archive/",
    "/tag-archive/",
    "/collection-archive/",
    "/page-archive/",
]

# Leftover academicpages boilerplate. Any hit means the template was not customized.
PLACEHOLDERS = [
    "Short biography for the left-hand sidebar",
    "yourorcidurl",
    "john+snow",
    "Paper Title Number",
    "This is a page not in th emain menu",
    "500x300.png",
    "bio-photo",
]


def page_path(route):
    """Map a site route to the file Jekyll wrote for it."""
    route = unquote(urlparse(route).path)
    if route.endswith("/"):
        return os.path.join(SITE, route.lstrip("/"), "index.html")
    return os.path.join(SITE, route.lstrip("/"))


def read(route):
    with open(page_path(route), encoding="utf-8") as fh:
        return fh.read()


def nav_items(body):
    block = re.search(r'visible-links">(.*?)</ul>', body, re.S)
    if not block:
        return []
    links = re.findall(r"<a [^>]*>([^<]*)</a>", block.group(1))
    return [html.unescape(t).strip() for t in links if t.strip()]


def check_pages(fail):
    for route, needle in EXPECTED_PAGES.items():
        if not os.path.isfile(page_path(route)):
            fail(f"{route} was not built (expected {page_path(route)})")
            continue
        body = read(route)
        if needle not in body:
            fail(f"{route} is missing expected content {needle!r}")


def check_nav(fail):
    body = read("/")
    # nav_items[0] is the masthead site title, the rest are the menu.
    items = nav_items(body)[1:]
    if items != EXPECTED_NAV:
        fail(f"nav is {items}, expected {EXPECTED_NAV}")


def check_removed(fail):
    for route in REMOVED_ROUTES:
        if os.path.isfile(page_path(route)):
            fail(f"{route} is still published; it should have been removed")


def check_author_links(fail):
    """The sidebar social links come from _config.yml author.*, easy to leave on the demo values."""
    body = read("/")
    sidebar = re.search(r'author__urls-wrapper.*?</ul>', body, re.S)
    sidebar = sidebar.group(0) if sidebar else ""
    for expected in ("https://github.com/bzin22", "mailto:bz297@cornell.edu", "linkedin.com/in/bryan-zin"):
        if expected not in sidebar:
            fail(f"sidebar is missing author link {expected!r}")
    if "github.com/academicpages/academicpages.github.io" in sidebar:
        fail("sidebar GitHub link still points at the academicpages template")


def check_placeholders(fail):
    for route in EXPECTED_PAGES:
        body = read(route)
        for text in PLACEHOLDERS:
            if text in body:
                fail(f"{route} still contains template placeholder {text!r}")


def check_escaped_pipes(fail):
    """Kramdown renders a bare \\| literally outside tables, showing "Founder \\| 2026"."""
    for route in EXPECTED_PAGES:
        body = read(route)
        article = re.search(r"<article.*?</article>", body, re.S)
        text = re.sub(r"<[^>]+>", " ", article.group(0) if article else body)
        if "\\|" in text:
            fail(rf"{route} renders a literal backslash-pipe; pipes need no escaping here")


def check_titles(fail):
    for route, expected in EXPECTED_TITLES.items():
        found = re.search(r"<title>(.*?)</title>", read(route), re.S)
        actual = html.unescape(found.group(1)).strip() if found else None
        if actual != expected:
            fail(f"{route} title is {actual!r}, expected {expected!r}")


def check_internal_links(fail):
    """Every internal href/src on every page must resolve to a file in _site."""
    for route in list(EXPECTED_PAGES) + ["/sitemap/", "/404.html"]:
        if not os.path.isfile(page_path(route)):
            continue
        body = read(route)
        for raw in re.findall(r'(?:href|src)="([^"]+)"', body):
            target = html.unescape(raw)
            if target.startswith(("http://", "https://", "//", "mailto:", "#", "data:", "javascript:")):
                continue
            resolved = urljoin(route, target)
            path = page_path(resolved)
            if not os.path.exists(path) and not os.path.isfile(path.rstrip("/")):
                fail(f"{route} links to {target}, which is not in _site")


def main():
    if not os.path.isdir(SITE):
        print(f"FAIL: {SITE} does not exist; run `bundle exec jekyll build` first")
        return 1

    failures = []
    fail = failures.append
    for check in (
        check_pages,
        check_nav,
        check_author_links,
        check_removed,
        check_placeholders,
        check_escaped_pipes,
        check_titles,
        check_internal_links,
    ):
        check(fail)

    for message in failures:
        print(f"FAIL: {message}")
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("OK: 6 pages, nav order, titles, assets, links, no template leftovers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
