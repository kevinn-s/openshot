import types
import unittest

from qt_api import QApplication, QAction, QLineEdit, QListView, QSizePolicy, QWidget

from windows.views.editor_panel import EditorPanel, EditorSection


class MemorySettings:
    def __init__(self):
        self.values = {"editor_active_section": "elements"}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value


class EditorPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = QWidget()
        for action_name in (
                "actionImportFiles", "actionTitle", "actionAnimatedTitle", "actionGenerate"):
            setattr(self.window, action_name, QAction(self.window))
        self.settings = MemorySettings()
        self.filters = {
            name: QLineEdit(self.window)
            for name in ("elements", "transitions", "emojis", "effects", "properties")
        }
        self.views = {
            name: QListView(self.window)
            for name in ("elements", "transitions", "emojis", "effects")
        }
        self.contents = {
            name: QWidget(self.window)
            for name in ("elements", "transitions", "emojis", "effects", "properties")
        }
        self.panel = EditorPanel(
            self.window, self.settings, str, self.contents, self.filters, self.views)

    def tearDown(self):
        self.panel.deleteLater()
        self.window.deleteLater()

    def test_navigation_uses_one_canonical_active_section(self):
        emitted = []
        self.panel.activeSectionChanged.connect(emitted.append)

        self.panel.set_active_section(EditorSection.EFFECTS)

        self.assertEqual(self.panel.active_section, "effects")
        self.assertIs(self.panel.stack.currentWidget(), self.panel.pages["effects"])
        self.assertEqual(
            [key for key, button in self.panel.section_buttons.items() if button.isChecked()],
            ["effects"],
        )
        self.assertEqual(self.settings.get("editor_active_section"), "effects")
        self.assertEqual(emitted, ["effects"])

    def test_search_queries_are_stored_per_section_and_route_to_existing_filters(self):
        self.panel.set_active_section("assets")
        self.panel.pages["assets"].search.setText("intro")
        self.assertEqual(self.filters["elements"].text(), "intro")

        self.panel.set_active_section("elements")
        self.panel.pages["elements"].search.setText("slide")
        self.assertEqual(self.filters["transitions"].text(), "slide")

        self.panel.set_active_section("effects")
        self.panel.pages["effects"].search.setText("blur")
        self.assertEqual(self.filters["effects"].text(), "blur")

        self.panel.set_active_section("assets")
        self.assertEqual(self.panel.pages["assets"].search.text(), "intro")
        self.assertEqual(self.filters["elements"].text(), "intro")

    def test_rail_remains_available_when_context_is_collapsed(self):
        self.panel.collapse_context()
        self.assertTrue(self.panel.context.isHidden())
        self.assertFalse(self.panel.section_buttons["elements"].isHidden())

        self.panel.set_active_section("tools")
        self.assertFalse(self.panel.context.isHidden())
        self.assertEqual(self.panel.active_section, "tools")

    def test_assets_page_has_no_media_category_button(self):
        assets = self.panel.pages["assets"]

        self.assertFalse(hasattr(assets, "category_buttons"))
        self.assertIs(assets.media_filter, self.filters["elements"])
        self.panel.set_active_section("assets")
        assets.search.setText("video")
        self.assertEqual(self.filters["elements"].text(), "video")

    def test_assets_import_button_triggers_existing_import_action(self):
        triggered = []
        self.window.actionImportFiles.triggered.connect(lambda: triggered.append(True))

        button = self.panel.pages["assets"].import_button
        self.assertEqual(button.text(), "Import File")
        self.assertEqual(button.sizePolicy().horizontalPolicy(), QSizePolicy.Expanding)

        button.click()

        self.assertEqual(triggered, [True])

    def test_properties_page_keeps_content_without_search_or_shortcut_grid(self):
        page = self.panel.pages["properties"]

        self.assertFalse(hasattr(page, "search"))
        self.assertFalse(hasattr(page, "card_grid"))
        self.assertTrue(self.filters["properties"].isHidden())
        self.assertIs(self.contents["properties"].parentWidget(), page)

    def test_tools_use_full_width_horizontal_cards(self):
        cards = self.panel.pages["tools"].card_grid.cards
        positions = [
            self.panel.pages["tools"].card_grid.grid.getItemPosition(index)[:2]
            for index in range(len(cards))
        ]
        self.assertEqual(positions, [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)])
        self.assertEqual([card.objectName() for card in cards], ["editorToolCard"] * 5)

    def test_youtube_embed_stays_inside_tools_panel(self):
        tools = self.panel.pages["tools"]
        self.panel.set_active_section(EditorSection.TOOLS)

        tools.card_grid.cards[-1].click()

        self.assertFalse(tools.youtube_page.isHidden())
        self.assertTrue(tools.tools_main_page.isHidden())
        self.assertFalse(self.panel.tool_back.isHidden())
        self.assertEqual(self.panel.title.text(), "YouTube Embed")

        self.panel.tool_back.click()
        self.assertTrue(tools.youtube_page.isHidden())
        self.assertFalse(tools.tools_main_page.isHidden())
        self.assertEqual(self.panel.title.text(), "Tools")

    def test_browser_list_views_use_horizontal_two_column_flow(self):
        self.panel.resize(360, 420)
        self.panel.show()
        self.app.processEvents()

        for view in self.views.values():
            self.assertEqual(view.flow(), QListView.LeftToRight)
            self.assertGreater(view.gridSize().width(), 0)


if __name__ == "__main__":
    unittest.main()
