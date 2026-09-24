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

# permalink -> text that must appear in the rendered page body.
# "/" is the workbench (index.html, its own layout). The plain Home moved to /about/.
EXPECTED_PAGES = {
    "/": "Tidy desk",
    "/about/": "Selected work",
    "/research/": "Supply-chain language and stock-market reactions",
    "/projects/": "Technical preparation",
    "/experience/": "Reframe Innovations",
    "/resume/": 'src="/images/bryan-zin-resume.png?v=2"',
}

# permalink -> exact <title> text. The home page's page.title equals site.title,
# so it must render the name once, not "Bryan Zin Bryan Zin" or "About Me Bryan Zin".
EXPECTED_TITLES = {
    "/": "Bryan Zin",
    "/about/": "Bryan Zin",
    "/research/": "Research Bryan Zin",
    "/projects/": "Projects Bryan Zin",
    "/experience/": "CV Bryan Zin",
    "/resume/": "Resume Bryan Zin",
}

# Old routes that must now be redirect stubs to another page, not pages of their own.
EXPECTED_REDIRECTS = {
    "/contact/": "/about/",
    "/cv/": "/resume/",
}

# route -> snippets of approved content that must be rendered exactly.
EXPECTED_SNIPPETS = {
    "/about/": [
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
    "/projects/": ['<p><a href="https://github.com/bzin22/adam-optimizer-recreation">Repository</a></p>'],
    "/resume/": ['<a href="/files/bryan-zin-cv.pdf">Download my resume (PDF)</a>'],
    # The workbench uses the site's own images and PDF, and its sun leads back to the plain site.
    "/": [
        'src="/images/bryan-zin.png"',
        'src="/images/scrisk-result.png"',
        'src="/images/bryan-zin-resume.png?v=2"',
        'href="/files/bryan-zin-cv.pdf"',
        '<a class="sun" href="/about/" data-tip="If you prefer something plainer"',
        '<button class="tidy" type="button" id="tidy" aria-pressed="false"',
        # Badge matches the plain sidebar.
        '<p class="bio">Independent researcher, YC founder, Apple Engineer</p>',
        '<p class="edu">Cornell University · B.S. in Mechanical Engineering</p>',
        '<a href="mailto:bz297@cornell.edu">Email</a>',
        '<span class="paperclip"></span>\n      <p class="cover-title">Resume</p>',
        '<section class="obj win folder closed" id="freshfleet" aria-label="Freshfleet">',
        'id="p-freshfleet" data-tilt="-5" data-opens="freshfleet"',
    ],
}

# Pages rendered with the plain theme (masthead, sidebar, footer). Everything but the workbench.
PLAIN_PAGES = [route for route in EXPECTED_PAGES if route != "/"]

# Text removed from the workbench.
WORKBENCH_FORBIDDEN = ["SELF-HEALING", "24 PX GRID", "click to open", "cover-hint",
                       "index card", "lab notebook", "one page", ">bz297@cornell.edu<"]

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
    "Optimizer implementation",
    "Experiment results",
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
    """Rendered HTML for a route, or "" if it was not built (check_pages reports that)."""
    if not os.path.isfile(page_path(route)):
        return ""
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
    body = read("/about/")
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
    body = read("/about/")
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
        if not body:
            continue  # check_pages already reports the missing page
        for snippet in snippets:
            if snippet not in body:
                fail(f"{route} is missing {snippet!r}")


def check_sidebar_bio(fail):
    """The sidebar is the one-line bio with the degree under it, same text as the workbench badge."""
    body = read("/about/")
    content = re.search(r'author__content">(.*?)</div>', body, re.S)
    content = content.group(1) if content else ""
    for expected in ('<p class="author__bio">Independent researcher, YC founder, Apple Engineer</p>',
                     '<p class="author__bio author__education">Cornell University · B.S. in Mechanical Engineering</p>'):
        if expected not in content:
            fail(f"sidebar is missing {expected!r}")
    if "Previously at Apple" in content:
        fail("sidebar still contains 'Previously at Apple'")


def check_footer(fail):
    """The footer is only the copyright line and the last-updated date.

    No follow row (GitHub is already in the sidebar), no Jekyll/AcademicPages credit, no sitemap link.
    """
    for route in PLAIN_PAGES:
        footer = re.search(r'<div class="page__footer">.*?</footer>', read(route), re.S)
        footer = footer.group(0) if footer else ""
        if not re.search(r"&copy; \d{4} Bryan Zin<br />", footer):
            fail(f"{route} footer does not read '© <year> Bryan Zin'")
        if not re.search(r"Site last updated \d{4}-\d{2}-\d{2}\s*</div>", footer):
            fail(f"{route} footer lost 'Site last updated <date>' or has something after it")
        for gone in ("page__footer-follow", "Powered by", "Jekyll", "AcademicPages", "Minimal Mistakes", "Sitemap", "/sitemap/"):
            if gone in footer:
                fail(f"{route} footer still contains {gone!r}")


def check_forbidden_text(fail):
    for route in EXPECTED_PAGES:
        article = re.search(r"<article.*?</article>", read(route), re.S)
        text = article.group(0) if article else ""
        for phrase in FORBIDDEN_TEXT:
            if phrase in text:
                fail(f"{route} still contains removed text {phrase!r}")


def check_workbench_removed(fail):
    body = read("/")
    for phrase in WORKBENCH_FORBIDDEN:
        if phrase in body:
            fail(f"/ still shows {phrase!r}")
    # Freshfleet has its own folder on the workbench, so the Projects folder no longer carries it.
    projects = re.search(r'<section [^>]*id="projects".*?</section>', body, re.S)
    if projects and "Freshfleet" in projects.group(0):
        fail("/ Projects folder still contains Freshfleet")
    fresh = re.search(r'<section [^>]*id="freshfleet".*?</section>', body, re.S)
    if not fresh or "UR10e robot arm" not in fresh.group(0):
        fail("/ Freshfleet folder is missing its write-up")


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


def check_sun_tooltip(fail):
    """The sun button keeps its icon, offers the fancier design on hover, and links to the workbench."""
    for route in PLAIN_PAGES:
        toggle = re.search(r'<li id="fancy-link".*?</li>', read(route), re.S)
        toggle = toggle.group(0) if toggle else ""
        if '<a href="/" ' not in toggle:
            fail(f"{route} sun button does not link to the workbench at /")
        if 'data-tooltip="If you prefer something fancier"' not in toggle:
            fail(f"{route} sun button is missing the 'If you prefer something fancier' tooltip")
        if "fa-sun" not in toggle:
            fail(f"{route} sun button lost its sun icon")
        if "toggle theme" in toggle:
            fail(f"{route} sun button still says 'toggle theme'")


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
        check_sidebar_bio,
        check_footer,
        check_forbidden_text,
        check_placeholders,
        check_workbench_removed,
        check_escaped_pipes,
        check_sun_tooltip,
        check_titles,
        check_internal_links,
    ):
        check(fail)

    for message in failures:
        print(f"FAIL: {message}")
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("OK: workbench + 5 plain pages, nav order, titles, redirects, figure, resume link, assets, links, no template leftovers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
