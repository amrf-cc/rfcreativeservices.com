"""Tests for the generated site. Run: python3 -m unittest discover -s tests -v"""
import html
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(name):
    with open(ROOT / name) as f:
        return json.load(f)


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a" and d.get("href"):
            self.links.append(d["href"])
        if tag in ("img", "script") and d.get("src"):
            self.links.append(d["src"])
        if tag == "link" and d.get("href"):
            self.links.append(d["href"])
        if tag in ("video", "source") and d.get("src"):
            self.links.append(d["src"])
        if tag == "video" and d.get("poster"):
            self.links.append(d["poster"])


def local_links(html_path):
    parser = LinkExtractor()
    parser.feed(html_path.read_text())
    out = []
    for link in parser.links:
        if link.startswith(("http://", "https://", "mailto:", "#", "data:", "//")):
            continue
        target = (html_path.parent / link.split("?")[0].split("#")[0])
        out.append(target.resolve())
    return out


def generated_pages():
    pages = [ROOT / n for n in ("index.html", "gallery.html", "contact.html", "404.html")]
    pages += sorted((ROOT / "gallery").glob("*.html"))
    return pages


class TestSiteGenerated(unittest.TestCase):
    def setUp(self):
        if not (ROOT / "index.html").exists():
            self.skipTest("site not built yet — run python3 build.py")

    def test_all_expected_pages_exist(self):
        projects = load("projects.json")["projects"]
        index_text = (ROOT / "index.html").read_text()
        # The About section (site-config.json bio prose) legitimately mentions
        # hidden clients such as 'Bodeguita Manolo', "McDonald's" and 'Pepsi';
        # that copy is a content decision outside this task, so strip it before
        # checking index.html for hidden client names.
        index_without_about = re.sub(r'<section class="about".*?</section>',
                                     "", index_text, flags=re.DOTALL)
        gallery_text = (ROOT / "gallery.html").read_text()
        for p in projects:
            page = ROOT / "gallery" / (p["slug"] + ".html")
            if p.get("hidden"):
                self.assertFalse(page.exists(),
                                 "hidden project has a page: %s" % page)
                link = "gallery/%s.html" % p["slug"]
                self.assertNotIn(link, index_text,
                                 "hidden project link in index.html: %s" % link)
                self.assertNotIn(link, gallery_text,
                                 "hidden project link in gallery.html: %s" % link)
                name = p.get("client", "")
                if name:
                    for candidate in {name, html.escape(name, quote=True)}:
                        self.assertNotIn(candidate, index_without_about,
                                         "hidden client %r in index.html" % name)
                        self.assertNotIn(candidate, gallery_text,
                                         "hidden client %r in gallery.html" % name)
            else:
                self.assertTrue(page.exists(), "missing %s" % page)
        for n in ("index.html", "gallery.html", "contact.html", "404.html"):
            self.assertTrue((ROOT / n).exists(), "missing %s" % n)

    def test_hidden_projects_are_off_the_site(self):
        projects = load("projects.json")["projects"]
        visible = [p for p in projects if not p.get("hidden")]
        for p in projects:
            if p.get("hidden"):
                page = ROOT / "gallery" / (p["slug"] + ".html")
                self.assertFalse(page.exists(), "hidden page exists: %s" % page)
        gallery_text = (ROOT / "gallery.html").read_text()
        self.assertEqual(gallery_text.count('class="card"'), len(visible),
                         "gallery.html should have one card per visible project")

    def test_no_broken_local_links(self):
        # 404.html uses root-absolute paths (allowed: GitHub Pages serves it
        # only at the domain root), so its "/" links are not repo-relative.
        skip = {"404.html"}
        broken = []
        for page in generated_pages():
            if not page.exists() or page.name in skip:
                continue
            for target in local_links(page):
                if not target.exists():
                    broken.append("%s -> %s" % (page.name, target))
        self.assertEqual(broken, [], "Broken links:\n" + "\n".join(broken))

    def test_no_absolute_root_paths(self):
        """Root-relative paths (/assets/...) break on the github.io subpath."""
        # 404.html is the one page allowed root-absolute paths: GitHub Pages
        # serves it only at the domain root, so "/assets/..." and "/" are correct there.
        skip = {"404.html"}
        for page in generated_pages():
            if not page.exists() or page.name in skip:
                continue
            text = page.read_text()
            hits = re.findall(r'(?:href|src|poster)="/(?!/)', text)
            self.assertEqual(hits, [], "root-relative URLs in %s" % page.name)

    def test_cname(self):
        self.assertEqual((ROOT / "CNAME").read_text().strip(), "riveraferran.com")

    def test_contact_form_present_on_index_and_contact(self):
        config = load("site-config.json")
        for page in (ROOT / "index.html", ROOT / "contact.html"):
            text = page.read_text()
            self.assertIn("contact-form", text)
            self.assertIn(config["email"], text)
            self.assertIn("_gotcha", text)  # honeypot

    def test_featured_projects_on_landing(self):
        projects = load("projects.json")["projects"]
        text = (ROOT / "index.html").read_text()
        for p in projects:
            if p.get("featured") and not p.get("hidden"):
                self.assertIn(html.escape(p["client"], quote=True), text)

    def test_video_block_per_project_with_videos(self):
        projects = load("projects.json")["projects"]
        visible = set(p["slug"] for p in projects if not p.get("hidden"))
        manifest = load("assets-manifest.json")
        for slug, data in manifest["projects"].items():
            if slug not in visible:
                continue
            for v in data["videos"]:
                livid = v.get("livid") or ""
                mp4 = v.get("mp4") or ""
                if not livid and not mp4:
                    # A video with neither a Livid embed nor an mp4 renders
                    # nothing, so it must not be asserted here.
                    continue
                text = (ROOT / "gallery" / (slug + ".html")).read_text()
                rendered = (livid and livid in text) or (mp4 and mp4 in text)
                self.assertTrue(rendered, "no video rendered on %s" % slug)


if __name__ == "__main__":
    unittest.main()
