import importlib.util
import unittest
from pathlib import Path

module_spec = importlib.util.spec_from_file_location("make_gallery", Path(__file__).with_name("make_gallery.py"))
gallery = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(gallery)


def scenario(**extra):
    return {"title": "Normal", "url": "/?state=normal", **extra}


class GalleryTests(unittest.TestCase):
    def test_numbered_contents_and_purpose(self):
        page = gallery.render({"groups": [{"title": "Profile", "description": "First visit", "scenarios": [scenario(), scenario()]}]})
        self.assertIn('<ol class="contents-list">', page)
        self.assertIn('href="#g1"', page)
        self.assertIn('class="number">01<', page)
        self.assertIn('class="scenario-number">1.2<', page)
        self.assertEqual(page.count("First visit"), 2)

    def test_no_manual_zoom(self):
        page = gallery.render({"scenarios": [scenario()]})
        for token in ("data-zoom", "localStorage", "100%</button>", "75%</button>", "50%</button>"):
            self.assertNotIn(token, page)

    def test_flat_and_unnamed_groups(self):
        page = gallery.render({"scenarios": [scenario()]})
        self.assertIn('id="g1"', page)
        self.assertIn("Screens", page)
        self.assertEqual(page.count("<iframe "), 1)

    def test_empty_groups_do_not_leave_numbering_gaps(self):
        page = gallery.render({"groups": [{"title": "Empty", "scenarios": []}, {"scenarios": [scenario()]}]})
        self.assertIn('id="g1"', page)
        self.assertNotIn('id="g2"', page)
        self.assertNotIn("Empty", page)

    def test_escaping_and_long_titles(self):
        title = '<script>"&' + "Long title " * 40
        page = gallery.render({"title": title, "lead": "<b>Fake</b>", "groups": [{"title": title, "description": "<img>", "scenarios": [scenario(title=title, note="<b>note</b>", url='/?a="&b=1')]}]})
        self.assertIn(gallery.esc(title), page)
        self.assertIn("&lt;img&gt;", page)
        self.assertIn("&lt;b&gt;note&lt;/b&gt;", page)
        self.assertIn('src="/?a=&quot;&amp;b=1"', page)
        self.assertNotIn('<script>"&', page)

    def test_locales_and_fallback(self):
        for lang, label in [("ru-RU", "Содержание"), ("en", "Contents"), ("de", "Contents")]:
            with self.subTest(lang=lang):
                self.assertIn(label, gallery.render({"lang": lang, "scenarios": [scenario()]}))

    def test_lazy_threshold_and_overrides(self):
        for count, override, expected in [(16, None, False), (17, None, True), (1, True, True), (17, False, False)]:
            spec = {"scenarios": [scenario() for _ in range(count)]}
            if override is not None:
                spec["lazy"] = override
            page = gallery.render(spec)
            self.assertEqual(page.count('loading="lazy"'), count if expected else 0)

    def test_real_viewports_and_automatic_fit(self):
        page = gallery.render({"frame": {"width": 390, "height": 844}, "max_width": 480, "scenarios": [scenario(), scenario(width=1280, height=800)]})
        self.assertIn('width="1280" height="800"', page)
        self.assertIn('width="390" height="844"', page)
        self.assertIn("ResizeObserver", page)
        self.assertIn('data-w="1280"', page)

    def test_invalid_specs(self):
        for spec in ({}, {"scenarios": [{"title": "Missing URL"}]}, {"scenarios": [scenario(width=0)]}, {"max_width": 0, "scenarios": [scenario()]}):
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                gallery.render(spec)


if __name__ == "__main__":
    unittest.main()
