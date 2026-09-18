import json
import os
import sys
import types
import unittest
from unittest.mock import patch


PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if PATH not in sys.path:
    sys.path.append(PATH)

from themes.manager import ThemeManager, ThemeName


class ThemeManagerTests(unittest.TestCase):
    def tearDown(self):
        ThemeManager._instance = None

    def test_bento_is_a_registered_theme(self):
        self.assertIs(ThemeName.find_by_name("Bento"), ThemeName.BENTO)
        self.assertEqual(
            ThemeName.get_sorted_theme_names(),
            ["Bento", "Cosmic Dusk", "Humanity: Dark", "Retro"],
        )

    def test_bento_theme_is_constructed_and_applied(self):
        class FakeBentoTheme:
            def __init__(self, app):
                self.app = app
                self.applied = False

            def apply_theme(self):
                self.applied = True

        module = types.ModuleType("themes.bento.theme")
        module.BentoTheme = FakeBentoTheme

        with patch.dict(sys.modules, {"themes.bento.theme": module}):
            theme = ThemeManager().apply_theme("Bento")

        self.assertEqual(theme.name, "Bento")
        self.assertTrue(theme.applied)

    def test_bento_is_default_and_packages_inter(self):
        settings_path = os.path.join(PATH, "settings", "_default.settings")
        with open(settings_path, encoding="utf-8") as settings_file:
            defaults = json.load(settings_file)
        theme = next(item for item in defaults if item.get("setting") == "theme")
        self.assertEqual(theme["value"], "Bento")

        font_dir = os.path.join(PATH, "themes", "bento", "fonts")
        self.assertTrue(os.path.isfile(os.path.join(font_dir, "Inter-VariableFont_wght.ttf")))
        self.assertTrue(os.path.isfile(os.path.join(font_dir, "OFL.txt")))


if __name__ == "__main__":
    unittest.main()
