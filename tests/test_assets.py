"""Tests for the asset pipeline. Run: python3 -m unittest discover -s tests -v"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ingest_media  # noqa: E402
import prepare_assets  # noqa: E402

HERO_PATHS = [
    "assets/img/acai-express/01.jpg",
    "assets/img/masthead",
    "assets/img/og-cover.jpg",
]


class TestSourcesExist(unittest.TestCase):
    def test_volume_mounted(self):
        if not prepare_assets.SOURCE_ROOT.exists():
            self.skipTest("Selected Works volume not mounted")

    def test_all_manifest_sources_exist(self):
        if not prepare_assets.SOURCE_ROOT.exists():
            self.skipTest("Selected Works volume not mounted")
        projects = prepare_assets.load_projects()
        missing = prepare_assets.check_sources(projects)
        self.assertEqual(missing, [], "Missing source files: %s" % missing)


class TestBuiltAssets(unittest.TestCase):
    """These fail until prepare_assets.py has been run for real."""

    def setUp(self):
        manifest_path = ROOT / "assets-manifest.json"
        if not manifest_path.exists():
            self.skipTest("assets-manifest.json not generated yet")
        self.manifest = json.loads(manifest_path.read_text())
        self.projects = prepare_assets.load_projects()

    def test_every_project_in_manifest(self):
        for p in self.projects:
            self.assertIn(p["slug"], self.manifest["projects"],
                          "%s missing from manifest" % p["slug"])

    def test_photo_counts_match_projects(self):
        for p in self.projects:
            entry = self.manifest["projects"][p["slug"]]
            self.assertEqual(len(entry["photos"]), len(p["photos"]),
                             "%s photo count differs between projects.json "
                             "and manifest" % p["slug"])

    def test_every_asset_file_exists_and_is_small(self):
        for slug, data in self.manifest["projects"].items():
            for photo in data["photos"]:
                full = ROOT / photo["full"]
                thumb = ROOT / photo["thumb"]
                self.assertTrue(full.exists(), "missing %s" % full)
                self.assertTrue(thumb.exists(), "missing %s" % thumb)
                self.assertLess(full.stat().st_size, 2 * 1024 * 1024,
                                "%s too big — recompress" % full)
            for video in data["videos"]:
                mp4 = video.get("mp4") or ""
                poster = video.get("poster") or ""
                # Livid-only videos have an empty mp4 (no self-hosted fallback).
                if mp4:
                    mp4_path = ROOT / mp4
                    self.assertTrue(mp4_path.exists(), "missing %s" % mp4_path)
                    self.assertLess(mp4_path.stat().st_size, 16 * 1024 * 1024,
                                    "%s too big — recompress" % mp4_path)
                if poster:
                    poster_path = ROOT / poster
                    self.assertTrue(poster_path.exists(),
                                    "missing %s" % poster_path)


class TestHeroUntouched(unittest.TestCase):
    def test_hero_unchanged(self):
        try:
            probe = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=str(ROOT), capture_output=True, text=True)
        except OSError:
            self.skipTest("git not available")
        if probe.returncode != 0 or probe.stdout.strip() != "true":
            self.skipTest("ROOT is not a git repository")
        result = subprocess.run(
            ["git", "diff", "--quiet", "HEAD", "--"] + HERO_PATHS,
            cwd=str(ROOT), capture_output=True)
        self.assertNotEqual(result.returncode, 1,
                            "hero/masthead/og-cover assets were modified")


class TestIngestIdempotent(unittest.TestCase):
    def test_nothing_to_ingest(self):
        if not ingest_media.MEDIA_ROOT.exists():
            self.skipTest("MEDIA_ROOT not mounted")
        manifest_path = ROOT / "assets-manifest.json"
        if not manifest_path.exists():
            self.skipTest("assets-manifest.json not generated yet")
        projects = json.loads((ROOT / "projects.json").read_text())
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(ingest_media.plan(projects, manifest), [])


if __name__ == "__main__":
    unittest.main()
