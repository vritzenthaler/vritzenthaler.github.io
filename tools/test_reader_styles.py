import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = (r'\.reader-paper \.ltx_section,\s*'
            r'\.reader-paper \.ltx_appendix,\s*'
            r'\.reader-paper \.ltx_bibliography')

class TestReaderStyles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = (ROOT / 'assets/css/reader.css').read_text()

    def test_deferred_sections_are_guarded_and_sized(self):
        self.assertIn('@supports (content-visibility: auto) and '
                      '(contain-intrinsic-block-size: auto 2000px) and '
                      'selector(html:has(> body.layout-reader))', self.css)
        self.assertRegex(self.css, SECTIONS + r'\s*\{\s*'
                         r'content-visibility: auto;\s*'
                         r'contain-intrinsic-block-size: auto 2000px;\s*\}')

    def test_anchor_scroll_is_instant_only_in_reader(self):
        self.assertRegex(self.css, r'html:has\(> body\.layout-reader\)\s*\{\s*'
                         r'scroll-behavior: auto;\s*\}')
        main = (ROOT / 'assets/css/main.css').read_text()
        self.assertRegex(main, r'html\s*\{\s*scroll-behavior: smooth;\s*\}')

    def test_print_uses_full_layout(self):
        self.assertIn('@media print', self.css)
        rules = self.css.split('@media print', 1)[1]
        self.assertRegex(rules, SECTIONS + r'\s*\{\s*'
                         r'content-visibility: visible;\s*'
                         r'contain-intrinsic-block-size: none;\s*\}')

if __name__ == '__main__':
    unittest.main()
