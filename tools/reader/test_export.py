#!/usr/bin/env python3
"""Tests for tools/reader/export.py. Self-contained, stdlib only."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export

ROOT = Path(__file__).resolve().parent
SITE = ROOT.parents[1]
PUB_FRAGMENT = SITE / "_includes" / "reader" / "cdo-maxwell.html"
PUB_MANIFEST = SITE / "_data" / "readers" / "cdo-maxwell.json"


def make_xhtml(tmp, inner):
    src = tmp / "in.xhtml"
    src.write_text(
        '<html xmlns="http://www.w3.org/1999/xhtml">'
        '<body><article class="ltx_document">' + inner +
        '</article></body></html>')
    return src


def iter_all(root, tag=None):
    for e in root.iter():
        if tag is None or e.tag == tag:
            yield e


def texts(root):
    return " ".join(t for t in root.itertext() if t)


class TestSerialization(unittest.TestCase):

    def test_tail_and_text_order_preserved(self):
        doc = ET.fromstring(
            '<div class="ltx_document"><p>before '
            '<math display="inline" alttext="x"><mi>x</mi></math> after '
            '<em>end</em></p></div>')
        export.wrap_inline_math(doc)
        w = [e for e in doc.iter()
             if "reader-inline-math" in (e.get("class") or "")][0]
        self.assertEqual([c.tag for c in w], ["math"])
        self.assertEqual(w.tail, " after ")
        self.assertIsNone(list(w)[0].tail)

    def test_tex_passed_unmodified(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            xhtml = make_xhtml(
                tmp, '<p><math display="inline" '
                     'alttext="\\text{ab%&#10;cd}"><mi>x</mi></math></p>')
            frag = export.extract_fragment(xhtml, "synthetic", tmp)
            w = [e for e in export.parse_fragment(frag).iter()
                 if e.get("data-renderer") == "katex"][0]
            mt = [t.text for t in w.iter("mtext") if t.text and t.text.strip()]
            self.assertIn("abcd", mt)
            self.assertNotIn("ab cd", mt)
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            xhtml = make_xhtml(
                tmp, '<p><math display="inline" '
                     'alttext="x%comment&#10;+y"><mi>x</mi></math></p>')
            frag = export.extract_fragment(xhtml, "synthetic", tmp)
            w = [e for e in export.parse_fragment(frag).iter()
                 if e.get("data-renderer") == "katex"][0]
            glyphs = " ".join("".join(m.itertext()) for m in w.iter("math"))
            self.assertIn("x", glyphs)
            self.assertIn("y", glyphs)
            self.assertNotIn("comment", glyphs)

    def test_normalization(self):
        cjs = ROOT / "render_math.cjs"

        def norm(tex):
            out = subprocess.run(
                ["node", "-e",
                 f'const m=require("{cjs}");'
                 "process.stdout.write(m.normalizeLatexmlTex(process.argv[1]))",
                 tex], capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            return out.stdout
        self.assertEqual(norm("\\bigl{(}x\\bigr{)}"), "\\bigl(x\\bigr)")
        self.assertEqual(norm("\\Bigg{\\langle}z"), "\\Bigg\\langle z")
        self.assertEqual(norm("a{b}"), "a{b}")
        self.assertEqual(norm("100\\% real"), "100\\% real")
        self.assertEqual(norm("x%gone\n+y"), "x+y")

    def test_unknown_macro_and_bad_delimiter_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            xhtml = make_xhtml(
                tmp, '<p><math display="inline" '
                     'alttext="\\NoSuchMacro{x}"><mi>x</mi></math></p>')
            with self.assertRaises(export.ConversionError):
                export.extract_fragment(xhtml, "synthetic", tmp)
        out = subprocess.run(
            ["node", str(ROOT / "render_math.cjs"), export.katex_js_path()],
            input=json.dumps(
                [{"id": "m", "tex": "\\bigl{ab}", "display": False}]),
            capture_output=True, text=True)
        self.assertNotEqual(out.returncode, 0)

    def test_classification_removed_keeps_neighbors(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            xhtml = make_xhtml(
                tmp,
                '<div class="ltx_abstract"><p class="ltx_p">Abs.</p></div>'
                '<div class="ltx_classification"><h6 class="ltx_title '
                'ltx_title_classification">2020 Mathematics Subject '
                'Classification: </h6>65M12</div>'
                '<div class="ltx_keywords">Keys</div>')
            text = export.extract_fragment(xhtml, "synthetic", tmp).read_text()
            self.assertNotIn("ltx_classification", text)
            self.assertNotIn("Mathematics Subject Classification", text)
            self.assertNotIn("65M12", text)
            self.assertIn("Abs.", text)
            self.assertIn("Keys", text)

    def test_svg_math_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            xhtml = make_xhtml(
                tmp, '<svg><foreignObject>'
                     '<math display="inline"><mi>s</mi></math>'
                     '</foreignObject></svg>')
            text = export.extract_fragment(xhtml, "synthetic", tmp).read_text()
            self.assertNotIn("data-renderer", text)
            self.assertIn("<math", text)

    def test_resources_same_basename(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "a").mkdir(); (tmp / "b").mkdir()
            (tmp / "a" / "p.png").write_bytes(b"A")
            (tmp / "b" / "p.png").write_bytes(b"B")
            xhtml = make_xhtml(
                tmp, '<img src="a/p.png"/><img src="b/p.png?v=1"/>')
            text = export.extract_fragment(xhtml, "synthetic", tmp).read_text()
            self.assertIn("/assets/reader/synthetic/a/p.png", text)
            self.assertIn("/assets/reader/synthetic/b/p.png?v=1", text)
            self.assertTrue((tmp / "resources" / "a" / "p.png").is_file())
            self.assertTrue((tmp / "resources" / "b" / "p.png").is_file())

    def test_missing_and_escaping_resources_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            outdir = tmp / "output"
            outdir.mkdir()
            outside = tmp / "outside.txt"
            outside.write_text("x")
            for inner in ('<img src="gone.png"/>',
                          '<img src="../outside.txt"/>'):
                with self.assertRaises(export.ConversionError):
                    export.extract_fragment(make_xhtml(outdir, inner),
                                            "synthetic", tmp)
            self.assertEqual(outside.read_text(), "x")

    def test_unsafe_markup_and_schemes_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            for inner in ('<script>alert(1)</script>',
                          '<a href="javascript:x">l</a>',
                          '<a href="mailto:someone@example.invalid">l</a>',
                          '<p onclick="x">t</p>',
                          '<span class="ltx_email">someone@example.invalid'
                          '</span>',
                          '<span class="ltx_address">x</span>'):
                frag = tmp / "f.html"
                frag.write_text(
                    '<div class="ltx_document">' + inner + '</div>')
                with self.assertRaises(export.ConversionError):
                    export.validate_article(frag)

    def test_duplicate_and_dangling_ids_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            frag = tmp / "f.html"
            frag.write_text('<div class="ltx_document">'
                            '<p id="x">a</p><p id="x">b</p></div>')
            with self.assertRaises(export.ConversionError):
                export.validate_article(frag)
            frag.write_text('<div class="ltx_document">'
                            '<a href="#none">1</a></div>')
            with self.assertRaises(export.ConversionError):
                export.validate_article(frag)

    def test_slug_and_diagnostics_validation(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            xhtml = make_xhtml(tmp, "<p>ok</p>")
            for slug in ("../x", "Bad_Slug", "a//b", "-x"):
                with self.assertRaises(export.ConversionError):
                    export.export_reader(xhtml, slug, site=tmp / "s")
            bad_diag = tmp / "d.json"
            bad_diag.write_text('{"errors": ["Error:undefined"], '
                                '"warnings": []}')
            with self.assertRaises(export.ConversionError):
                export.export_reader(xhtml, "ok-slug", site=tmp / "s",
                                     diagnostics=json.loads(
                                         bad_diag.read_text()))

    def test_failure_keeps_existing_public_files(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            site = tmp / "s"
            (site / "_includes" / "reader").mkdir(parents=True)
            (site / "_data" / "readers").mkdir(parents=True)
            old = '<div class="ltx_document">old</div>'
            (site / "_includes" / "reader" / "ok-slug.html").write_text(old)
            (site / "_data" / "readers" / "ok-slug.json").write_text("{}")
            xhtml = make_xhtml(
                tmp, '<p><math display="inline" '
                     'alttext="\\Bogus{x}"><mi>x</mi></math></p>')
            with self.assertRaises(export.ConversionError):
                export.export_reader(xhtml, "ok-slug", site=site)
            self.assertEqual(
                (site / "_includes" / "reader" / "ok-slug.html").read_text(),
                old)
            self.assertEqual(
                (site / "_data" / "readers" / "ok-slug.json").read_text(),
                "{}")


    def test_export_into_fresh_site(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            xhtml = make_xhtml(tmp, '<p><math display="inline" '
                               'alttext="x"><mi>x</mi></math></p>')
            new_site = tmp / "new-site"
            out = export.export_reader(xhtml, "ok-slug", site=new_site)
            self.assertTrue((new_site / "build" / "reader").is_dir())
            manifest = json.loads(
                (new_site / "_data" / "readers" / "ok-slug.json").read_text())
            self.assertEqual(manifest["sha256"], export.sha256(out))
            self.assertEqual(manifest["fragment"], "reader/ok-slug.html")
            self.assertFalse(manifest["warning"])
            self.assertFalse((new_site / "build" / "reader" /
                              "export-").exists())

    def test_invalid_cli_combo_skips_latexml(self):
        fake = tempfile.mkdtemp()
        out = subprocess.run(
            [sys.executable, str(ROOT / "export.py"), "--slug", "ok-slug",
             "--source", "/nonexistent", "--diagnostics", "/nonexistent.json"],
            capture_output=True, text=True)
        self.assertEqual(out.returncode, 1)
        self.assertIn("--diagnostics", out.stderr)
        self.assertFalse((export.BUILD / "source").exists())


class TestPublishedArtifact(unittest.TestCase):

    def test_fragment_matches_manifest_hash(self):
        self.assertTrue(PUB_FRAGMENT.is_file(), "no exported artifact")
        manifest = json.loads(PUB_MANIFEST.read_text())
        self.assertEqual(manifest["sha256"], export.sha256(PUB_FRAGMENT))
        export.validate_article(PUB_FRAGMENT)
        self.assertEqual(manifest["math_renderer"], "katex")
        self.assertEqual(manifest["fragment"], "reader/cdo-maxwell.html")

    def test_formula_count_and_refs(self):
        root = export.parse_fragment(PUB_FRAGMENT)
        maths = [e for e in iter_all(root)
                 if e.get("data-renderer") == "katex"]
        self.assertEqual(len(maths), 1171)
        ids = {e.get("id") for e in maths}
        self.assertEqual(len(ids), 1171)
        for e in maths:
            self.assertTrue(any("katex-html" in (d.get("class") or "")
                                for d in e.iter()))


if __name__ == "__main__":
    unittest.main()
