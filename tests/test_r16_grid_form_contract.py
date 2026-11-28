"""R16 v2 source guard; real browser layout belongs to P4541.

The v1 uniform desktop density/palette proposal was never adopted. Preserve
the baseline sizing and full-workspace dark labels, while checking the new
compact contrast, explicit keyboard focus and measured mobile footer lane.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'geometry-web'


def rules(filename):
    text = (WEB / filename).read_text(encoding='utf-8')
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    rows = []
    for match in re.finditer(r'([^{}]+)\{([^{}]*)\}', text):
        selectors = [' '.join(s.split()) for s in match[1].split(',')]
        properties = {}
        for statement in match[2].split(';'):
            if ':' in statement:
                key, value = statement.split(':', 1)
                properties[key.strip()] = ' '.join(value.split())
        rows.append((selectors, properties))
    return rows


def values(filename, selector, property_name):
    return [p[property_name] for selectors, p in rules(filename)
            if selector in selectors and property_name in p]


def contrast(a, b):
    def luminance(color):
        channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        return sum((v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4) * w
                   for v, w in zip(channels, (.2126, .7152, .0722)))
    low, high = sorted([luminance(a), luminance(b)])
    return (high + .05) / (low + .05)


class GridFormContract(unittest.TestCase):
    def exact(self, file, selector, prop, expected, marker):
        self.assertEqual(values(file, selector, prop), expected, marker + ': ' + selector + ' ' + prop)

    def test_compact_labels_use_existing_root_muted_with_contrast(self):
        self.exact('grid-inspector.css', '.gi-inspector label', 'color', ['var(--form-label-color)'],
                   'R16GF_LABEL_ROOT_TOKEN')
        color = values('app.css', ':root', '--muted')
        self.assertEqual(len(color), 1, 'R16GF_EXISTING_MUTED')
        self.assertGreaterEqual(contrast(color[0], '#ffffff'), 4.5, 'R16GF_LABEL_CONTRAST')

    def test_label_alias_is_resolved_once_in_root_before_body_inheritance(self):
        # Inspect every stylesheet actually linked by the App, including body
        # overrides. The real computed-color equality remains in P4541.
        index = (WEB / 'index.html').read_text(encoding='utf-8')
        names = re.findall(r'<link\b[^>]*href="([^"?]+\.css)(?:\?[^"]*)?"', index)
        self.assertIn('app.css', names, 'R16GF_ROOT_STYLESHEET_LOADED')
        declarations = [(name, selectors, properties['--form-label-color'])
                        for name in names for selectors, properties in rules(name)
                        if '--form-label-color' in properties]
        self.assertEqual(declarations, [('app.css', [':root'], 'var(--muted)')],
                         'R16GF_ROOT_ALIAS_DECLARATION')

    def test_no_new_palette_or_workspace_override(self):
        self.assertFalse((WEB / 'grid-form-tokens.css').exists(), 'R16GF_NO_NEW_PALETTE')
        self.assertNotIn('grid-form-tokens.css', (WEB / 'index.html').read_text(encoding='utf-8'),
                         'R16GF_NO_NEW_PALETTE')
        self.exact('grid-system-workspace.css', '.ig-workspace', '--muted', ['#526579'],
                   'R16GF_EXISTING_SCOPE_ONLY')
        self.assertFalse(any('--grid-form-' in key for file in ['grid-inspector.css', 'grid-system-workspace.css']
                             for _, p in rules(file) for key in p), 'R16GF_NO_NEW_PALETTE')

    def test_original_desktop_and_mobile_density_preserved(self):
        for selector in ['.gi-inspector input', '.gi-inspector select']:
            self.exact('grid-inspector.css', selector, 'min-height', ['34px', '40px'], 'R16GF_DENSITY_PRESERVED')
            self.exact('grid-inspector.css', selector, 'font-size', ['14px', '14px'], 'R16GF_DENSITY_PRESERVED')
            self.exact('grid-inspector.css', selector, 'border-radius', ['5px'], 'R16GF_DENSITY_PRESERVED')
        for selector in ['.ig-settings input', '.ig-settings select']:
            self.exact('grid-system-workspace.css', selector, 'min-height', ['38px'], 'R16GF_DENSITY_PRESERVED')
            self.exact('grid-system-workspace.css', selector, 'border-radius', ['6px'], 'R16GF_DENSITY_PRESERVED')
        self.exact('grid-system-workspace.css', '.ig-workspace', '--ig-fh', ['38px', '44px'],
                   'R16GF_COMPOUND_DENSITY_PRESERVED')

    def test_full_dark_labels_and_original_sizes_preserved(self):
        self.exact('grid-system-workspace.css', '.ig-settings label', 'color', [], 'R16GF_FULL_INK_PRESERVED')
        self.exact('grid-system-workspace.css', '.ig-settings label', 'font-size', ['12px'], 'R16GF_FULL_INK_PRESERVED')
        self.exact('grid-system-workspace.css', '.ig-workspace', 'color', ['var(--ink)'], 'R16GF_FULL_INK_PRESERVED')
        self.exact('grid-system-workspace.css', '.ig-settings .ig-name input', 'font-size', ['13px'],
                   'R16GF_FULL_INK_PRESERVED')
        color = values('app.css', ':root', '--ink')[0]
        self.assertGreaterEqual(contrast(color, '#ffffff'), 12, 'R16GF_FULL_INK_PRESERVED')

    def test_keyboard_focus_including_compound_clip(self):
        for file, selectors in [
            ('grid-inspector.css', ['.gi-inspector input:focus-visible', '.gi-inspector select:focus-visible',
                                    '.gi-inspector button:focus-visible']),
            ('grid-system-workspace.css', ['.ig-settings input:focus-visible', '.ig-settings select:focus-visible',
                                           '.ig-settings button:focus-visible', '.ig-footer-actions button:focus-visible',
                                           '.ig-pf-box:has(input:focus-visible)'])]:
            for selector in selectors:
                self.exact(file, selector, 'outline', ['2px solid var(--accent)'], 'R16GF_FOCUS')
                self.exact(file, selector, 'outline-offset', ['2px'], 'R16GF_FOCUS')

    def test_measured_footer_lane_is_wired_and_keeps_left_edge(self):
        file, selector = 'workspace-height-dialogs.css', '#infiniteGridWorkspace .ig-inspector .ig-footer'
        self.exact(file, selector, 'inset', ['auto var(--r16-grid-scrollbar, 0px) 0 auto'], 'R16GF_FOOTER_GUTTER')
        self.exact(file, selector, 'width', ['calc(var(--r123h-dialog-dock) - var(--r16-grid-scrollbar, 0px))'],
                   'R16GF_FOOTER_GUTTER')
        source = (WEB / 'grid-system-workspace.js').read_text(encoding='utf-8')
        self.assertIn('        syncFooterLane();', source, 'R16GF_FOOTER_OBSERVER')
        self.assertIn("resizeWatch.observe(dialog.querySelector('.ig-layout'))", source, 'R16GF_FOOTER_OBSERVER')

    def test_invalid_disabled_and_main_mobile_floor_retained(self):
        self.exact('grid-system-workspace.css', '.ig-settings input[aria-invalid=true]', 'border-color',
                   ['var(--danger)'], 'R16GF_INVALID_RETAINED')
        self.exact('grid-inspector.css', '.gi-inspector .primary-button:disabled', 'cursor', ['wait'],
                   'R16GF_DISABLED_RETAINED')
        self.exact('grid-system-workspace.css', '.ig-footer-actions button:disabled', 'cursor', ['not-allowed'],
                   'R16GF_DISABLED_RETAINED')
        # Existing touch overrides remain at their original specificity.
        self.assertIn('#gridInlineInspector :is(.gi-actions .btn, input, select, .primary-button) { min-height: 44px; }',
                      (WEB / 'workspace-height.css').read_text(encoding='utf-8'), 'R16GF_MAIN_TOUCH_RETAINED')
        for selector in ['.ig-workspace button', '.ig-workspace input', '.ig-workspace select']:
            self.exact('grid-system-workspace.css', selector, 'min-height', ['44px'], 'R16GF_MAIN_TOUCH_RETAINED')


if __name__ == '__main__':
    unittest.main(verbosity=2)
