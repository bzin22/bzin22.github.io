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
# CV is the former Experience page and keeps /experience/. Contact was removed.
EXPECTED_NAV = ["Home", "Research", "Projects", "CV", "Resume"]

# permalink -> text that must appear in the rendered page body
EXPECTED_PAGES = {
    "/": "Selected work",
    "/research/": "Supply-chain language and stock-market reactions",
    "/projects/": "Technical preparation",
    "/experience/": "Reframe Innovations",
    "/resume/": 'src="/images/bryan-zin-resume.png?v=2"',
}

# permalink -> exact <title> text. The home page's page.title equals site.title,
# so it must render the name once, not "Bryan Zin Bryan Zin" or "About Me Bryan Zin".
EXPECTED_TITLES = {
    "/": "Bryan Zin",
    "/research/": "Research Bryan Zin",
    "/projects/": "Projects Bryan Zin",
    "/experience/": "CV Bryan Zin",
    "/resume/": "Resume Bryan Zin",
}

# Old routes that must now be redirect stubs to another page, not pages of their own.
EXPECTED_REDIRECTS = {
    "/contact/": "/",
    "/cv/": "/resume/",
}

# route -> snippets of approved content that must be rendered exactly.
EXPECTED_SNIPPETS = {
    "/": [
        'href="https://www.ycombinator.com/companies/usereframe"',
        'href="/research/">Research overview</a>',
        'href="/projects/">Selected projects</a>',
        'href="https://github.com/bzin22/adam-optimizer-recreation">Code and experiments</a>',
    ],
    "/research/": [
        'src="/images/scrisk-result.png"',
        'alt="Mean two-day abnormal returns decrease across fractional risk portfolios, from 0.52% in Q1 to −0.41% in Q5; error bars show firm-clustered 95% intervals."',
        "<figcaption>Mean CAR(0,1) by fractional SCRisk portfolio, 2010–2019. Bars show 95% intervals clustered by firm. Final sample: 52,533 calls from 2,026 firms. Portfolios share observations when scores are tied.</figcaption>",
    ],
    "/resume/": ['<a href="/files/bryan-zin-cv.pdf">Download my resume (PDF)</a>'],
}

# Content the approved copy removed, plus implementation notes that must never be published.
FORBIDDEN_TEXT = [
    "minor in Business",
    "FinBERT",
    "Word2Vec",
    "Matlab",
    "Research interests",
    "$1.2M",
    "$50M",
    "repository visibility",
    "private",
]

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


def check_redirects(fail):
    for route, target in EXPECTED_REDIRECTS.items():
        if not os.path.isfile(page_path(route)):
            fail(f"{route} was not built; it should redirect to {target}")
            continue
        body = read(route)
        refresh = re.search(r'http-equiv="refresh" content="0; url=([^"]+)"', body)
        if not refresh or urlparse(refresh.group(1)).path != target:
            fail(f"{route} does not redirect to {target}")
        if "<article" in body:
            fail(f"{route} renders a full page; it should only be a redirect stub")


def check_snippets(fail):
    for route, snippets in EXPECTED_SNIPPETS.items():
        body = read(route)
        for snippet in snippets:
            if snippet not in body:
                fail(f"{route} is missing {snippet!r}")


def check_sidebar_education(fail):
    body = read("/")
    if '<p class="author__education">Cornell University · B.S. in Mechanical Engineering</p>' not in body:
        fail("sidebar is missing the separate Cornell education line")


def check_forbidden_text(fail):
    for route in EXPECTED_PAGES:
        article = re.search(r"<article.*?</article>", read(route), re.S)
        text = article.group(0) if article else ""
        for phrase in FORBIDDEN_TEXT:
            if phrase in text:
                fail(f"{route} still contains removed text {phrase!r}")


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
        check_redirects,
        check_snippets,
        check_sidebar_education,
        check_forbidden_text,
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
    print("OK: 5 pages, nav order, titles, redirects, figure, resume link, assets, links, no template leftovers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
