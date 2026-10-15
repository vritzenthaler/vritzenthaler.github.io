import re
import unittest
from pathlib import Path

CSS = Path(__file__).resolve().parents[1] / 'assets' / 'css' / 'main.css'

class TestPageTransitions(unittest.TestCase):
    def test_crossfade_has_matching_timing_without_delay(self):
        css = CSS.read_text()
        animations = {}
        for state in ('old', 'new'):
            block = re.search(r'::view-transition-' + state + r'\(root\)\s*\{([^}]+)\}', css).group(1)
            animations[state] = re.search(r'animation:\s*([^;]+);', block).group(1).split()
        self.assertEqual(animations['old'][0], 'page-out')
        self.assertEqual(animations['new'][0], 'page-in')
        self.assertEqual(animations['old'][1:], ['0.5s', 'ease-in-out', 'both'])
        self.assertEqual(animations['new'][1:], animations['old'][1:])

if __name__ == '__main__':
    unittest.main()
