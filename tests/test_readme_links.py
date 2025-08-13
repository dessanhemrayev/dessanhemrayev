# ======================================================================
# Auto-generated tests: README link, image, and badge validation
# Testing library/framework: pytest
# These tests validate structure and correctness of links and images
# within README without performing network requests.
# ======================================================================

import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Precompiled regex patterns for simple HTML/Markdown parsing
ANCHOR_TAG_RE = re.compile(r'<a\\s+([^>]+)>', re.IGNORECASE)
IMG_TAG_RE = re.compile(r'<img\\s+([^>]+)>', re.IGNORECASE)
HREF_RE = re.compile(r'href="([^"]+)"', re.IGNORECASE)
SRC_RE = re.compile(r'src="([^"]+)"', re.IGNORECASE)
ALT_RE = re.compile(r'alt="([^"]*)"', re.IGNORECASE)
TARGET_BLANK_RE = re.compile(r'target="_blank"', re.IGNORECASE)
REL_NOREFFERER_RE = re.compile(r'rel="[^"]*\\bnoreferrer\\b[^"]*"', re.IGNORECASE)
WIDTH_RE = re.compile(r'width="(\\d+)"', re.IGNORECASE)
HEIGHT_RE = re.compile(r'height="(\\d+)"', re.IGNORECASE)
MARKDOWN_IMG_RE = re.compile(r'!\\[([^\\]]+)\\]\\(([^)\\s]+)\\)')
HEADING_RE = re.compile(r'^###\\s+(.+?)\\s*$', re.MULTILINE)


def _read_readme_text() -> str:
    """Load README content from common locations, preferring repository root."""
    candidates = [
        Path("README.md"),
        Path("Readme.md"),
        Path("readme.md"),
        Path("README.MD"),
        Path("README.rst"),
        Path("readme.rst"),
    ]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")
    # Fallback: search the repo for any README-like file
    for p in Path(".").rglob("README*.*"):
        try:
            return p.read_text(encoding="utf-8")
        except Exception:
            continue
    raise AssertionError("README file not found in repository.")


def _get_section(text: str, heading: str) -> str:
    """
    Extract the content of a section starting at '### {heading}' until the next '### ' or EOF.
    Asserts the heading exists.
    """
    # Find the start of the requested heading
    m = re.search(rf"^###\\s+{re.escape(heading)}\\s*$", text, flags=re.MULTILINE)
    assert m, f"Heading '### {heading}' not found in README."
    start = m.end()
    # Find the next heading after the current one
    m2 = re.search(r"^###\\s+", text[start:], flags=re.MULTILINE)
    end = start + (m2.start() if m2 else len(text) - start)
    return text[start:end]


def _extract_attr(pattern: re.Pattern, text: str):
    """Return list of attribute strings captured by pattern (e.g., contents of <a ...> or <img ...>)."""
    return pattern.findall(text)


def test_readme_exists_and_non_empty():
    readme = _read_readme_text()
    assert isinstance(readme, str) and readme.strip(), "README should exist and not be empty."


def test_no_insecure_http_urls_in_readme():
    readme = _read_readme_text()
    assert "http://" not in readme, "Avoid insecure http URLs; use https instead."


def test_all_links_and_images_use_absolute_https_urls():
    readme = _read_readme_text()
    urls = []

    for attrs in _extract_attr(ANCHOR_TAG_RE, readme):
        m = HREF_RE.search(attrs)
        if m:
            urls.append(m.group(1))

    for attrs in _extract_attr(IMG_TAG_RE, readme):
        m = SRC_RE.search(attrs)
        if m:
            urls.append(m.group(1))

    for _, u in MARKDOWN_IMG_RE.findall(readme):
        urls.append(u)

    assert urls, "No URLs found in README; expected anchors, images or badges."

    for url in urls:
        parsed = urlparse(url)
        assert parsed.scheme in ("http", "https"), f"URL must be absolute http(s): {url}"
        assert parsed.netloc, f"URL must include a host: {url}"
        assert parsed.scheme == "https", f"URL should use https: {url}"


def test_skills_section_images_have_alt_and_dimensions():
    readme = _read_readme_text()
    skills = _get_section(readme, "Skills")
    img_attrs = _extract_attr(IMG_TAG_RE, skills)
    assert img_attrs, "Expected <img> tags in Skills section."
    for attrs in img_attrs:
        alt = ALT_RE.search(attrs)
        assert alt, f"Image missing alt attribute in Skills: <img {attrs}>"
        assert alt.group(1).strip() != "", "Image alt text in Skills should not be empty."
        w = WIDTH_RE.search(attrs)
        h = HEIGHT_RE.search(attrs)
        assert w and h, "Images in Skills should declare width and height."
        assert int(w.group(1)) > 0 and int(h.group(1)) > 0, "Image dimensions must be positive."


def test_skills_section_anchor_links_external_with_target_blank_and_rel_noreferrer():
    readme = _read_readme_text()
    skills = _get_section(readme, "Skills")
    anchor_attrs = _extract_attr(ANCHOR_TAG_RE, skills)
    assert anchor_attrs, "Expected <a> tags in Skills section."
    for attrs in anchor_attrs:
        href_m = HREF_RE.search(attrs)
        assert href_m, f"Anchor missing href in Skills: <a {attrs}>"
        url = href_m.group(1)
        parsed = urlparse(url)
        assert parsed.scheme in ("http", "https") and parsed.netloc, f"Skills anchor should link externally: {url}"
        assert TARGET_BLANK_RE.search(attrs), "Skills anchor should include target=\"_blank\"."
        assert REL_NOREFFERER_RE.search(attrs), "Skills anchor should include rel=\"noreferrer\" (or include it among other rel values)."


def test_socials_links_have_target_blank_and_rel_noreferrer():
    readme = _read_readme_text()
    socials = _get_section(readme, "Socials")
    anchor_attrs = _extract_attr(ANCHOR_TAG_RE, socials)
    assert anchor_attrs, "Expected <a> tags in Socials section."
    for attrs in anchor_attrs:
        assert TARGET_BLANK_RE.search(attrs), "Social link should include target=\"_blank\"."
        assert REL_NOREFFERER_RE.search(attrs), "Social link should include rel=\"noreferrer\"."


def test_socials_picture_sources_define_media_and_srcset():
    readme = _read_readme_text()
    socials = _get_section(readme, "Socials")
    # Expect at least one <source> tag with media and srcset inside <picture>
    has_source = re.search(r'<source[^>]+media="[^"]+"[^>]+srcset="[^"]+"', socials, flags=re.IGNORECASE) is not None
    assert has_source, "Expected a <source> with both media and srcset attributes in Socials <picture>."


def test_badges_present_and_query_parameters_valid():
    readme = _read_readme_text()
    badges = _get_section(readme, "Badges")
    md_imgs = MARKDOWN_IMG_RE.findall(badges)
    assert len(md_imgs) >= 3, "Expected at least three badges (Top Langs, GitHub Stats, Streak)."

    urls = [u for _, u in md_imgs]

    # Top Languages badge
    top_langs = [u for u in urls if "github-readme-stats.vercel.app" in u and "/api/top-langs/" in u]
    assert top_langs, "Top Languages badge is missing."
    for u in top_langs:
        pu = urlparse(u)
        qs = parse_qs(pu.query)
        assert "username" in qs and qs["username"][0], "Top Languages badge must include ?username=..."

    # GitHub Stats badge
    stats = [u for u in urls if "github-readme-stats.vercel.app" in u and "/api?" in u and "/api/top-langs/" not in u]
    assert stats, "GitHub Stats badge is missing."
    for u in stats:
        pu = urlparse(u)
        qs = parse_qs(pu.query)
        assert "username" in qs and qs["username"][0], "GitHub Stats badge must include ?username=..."
        show = qs.get("show", [""])[0]
        for key in ["reviews", "discussions_started", "discussions_answered", "prs_merged", "prs_merged_percentage"]:
            assert key in show, f"Expected '{key}' in GitHub Stats badge 'show' parameter."

    # Streak badge
    streak = [u for u in urls if "github-readme-streak-stats.herokuapp.com" in u]
    assert streak, "GitHub Streak badge is missing."
    for u in streak:
        pu = urlparse(u)
        qs = parse_qs(pu.query)
        assert "user" in qs and qs["user"][0], "Streak badge must include ?user=..."
