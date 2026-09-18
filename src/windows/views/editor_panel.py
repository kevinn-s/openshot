"""Two-level editor sidebar used by the Bento workspace."""

import os

from qt_api import Qt, QSize, pyqtSignal
from qt_api import QIcon
from qt_api import (
    QAbstractItemView, QButtonGroup, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QListView, QScrollArea, QSizePolicy, QStackedWidget,
    QPushButton, QToolButton, QVBoxLayout, QWidget,
)

from classes import info
from windows.tools.youtube_embed import YoutubeEmbedPage


class EditorSection:
    ELEMENTS = "elements"
    ASSETS = "assets"
    EFFECTS = "effects"
    TOOLS = "tools"
    PROPERTIES = "properties"

    ALL = (ASSETS, ELEMENTS, EFFECTS, TOOLS, PROPERTIES)


def _bento_icon(name):
    return QIcon(os.path.join(info.PATH, "themes", "bento", "images", name))


class SearchField(QFrame):
    """Search input with a leading icon and a single visual surface."""

    textChanged = pyqtSignal(str)

    def __init__(self, placeholder, parent=None):
        super().__init__(parent)
        self.setObjectName("editorSearchField")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 8, 0)
        layout.setSpacing(6)

        icon = QIcon.fromTheme("edit-find")
        if icon.isNull():
            icon = _bento_icon("view-analysis.svg")
        icon_label = QLabel(self)
        icon_label.setObjectName("editorSearchIcon")
        icon_label.setPixmap(icon.pixmap(16, 16))
        layout.addWidget(icon_label)

        self.input = QLineEdit(self)
        self.input.setObjectName("editorBrowserSearch")
        self.input.setPlaceholderText(placeholder)
        self.input.setClearButtonEnabled(True)
        self.input.textChanged.connect(self.textChanged.emit)
        layout.addWidget(self.input, 1)

    def text(self):
        return self.input.text()

    def setText(self, text):
        self.input.setText(text)


class ContentCard(QToolButton):
    """Reusable icon-and-label card for editor content and actions."""

    def __init__(self, title, description="", icon=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.setObjectName("editorContentCard")
        self.setText(title)
        self.setToolTip(description or title)
        self.setAccessibleName(title)
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setIcon(icon or QIcon())
        self.setIconSize(QSize(28, 28))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(88)

    def matches(self, query):
        haystack = "%s %s" % (self.title, self.description)
        return query.lower() in haystack.lower()


class ToolCard(QToolButton):
    """Horizontal action card with a contained icon badge."""

    def __init__(self, title, description="", icon=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.setObjectName("editorToolCard")
        self.setToolTip(description or title)
        self.setAccessibleName(title)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(72)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 12, 8)
        layout.setSpacing(10)

        icon_badge = QFrame(self)
        icon_badge.setObjectName("editorToolIconBadge")
        icon_badge.setFixedSize(48, 48)
        icon_layout = QHBoxLayout(icon_badge)
        icon_layout.setContentsMargins(7, 7, 7, 7)
        icon_label = QLabel(icon_badge)
        icon_label.setObjectName("editorToolIcon")
        icon_label.setPixmap((icon or QIcon()).pixmap(34, 34))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_layout.addWidget(icon_label)
        layout.addWidget(icon_badge)

        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(2)
        title_label = QLabel(title, self)
        title_label.setObjectName("editorToolTitle")
        text.addWidget(title_label)
        if description:
            description_label = QLabel(description, self)
            description_label.setObjectName("editorToolDescription")
            description_label.setWordWrap(True)
            text.addWidget(description_label)
        text.addStretch(1)
        layout.addLayout(text, 1)

    def matches(self, query):
        haystack = "%s %s" % (self.title, self.description)
        return query.lower() in haystack.lower()


class CardGrid(QScrollArea):
    """Scrollable, filterable two-column collection of ContentCard widgets."""

    def __init__(self, parent=None, exclusive=False, columns=2):
        super().__init__(parent)
        self.setObjectName("editorCardBrowser")
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.container = QWidget(self)
        self.container.setObjectName("editorCardGrid")
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(8)
        self.grid.setVerticalSpacing(8)
        self.grid.setAlignment(Qt.AlignTop)
        self.setWidget(self.container)
        self.cards = []
        self.columns = columns
        self.group = QButtonGroup(self)
        self.group.setExclusive(exclusive)

    def add_card(self, title, description="", icon=None, callback=None, checkable=False):
        card_class = ToolCard if self.columns == 1 else ContentCard
        card = card_class(title, description, icon, self.container)
        card.setCheckable(checkable)
        if checkable:
            self.group.addButton(card)
        if callback:
            card.clicked.connect(lambda _checked=False, fn=callback: fn())
        self.cards.append(card)
        self._layout_cards()
        return card

    def set_filter(self, query):
        for card in self.cards:
            card.setVisible(card.matches(query))
        self._layout_cards()

    def _layout_cards(self):
        visible_cards = [card for card in self.cards if not card.isHidden()]
        for card in self.cards:
            self.grid.removeWidget(card)
        for index, card in enumerate(visible_cards):
            self.grid.addWidget(card, index // self.columns, index % self.columns)


class BrowserPage(QWidget):
    """Shared contextual-page shell with search and independently scrolling content."""

    queryChanged = pyqtSignal(str)

    def __init__(self, placeholder, content, parent=None, list_views=(), controls=()):
        super().__init__(parent)
        self.setObjectName("editorBrowserPage")
        self.list_views = tuple(list_views)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 12)
        layout.setSpacing(10)
        self.search = SearchField(placeholder, self)
        self.search.textChanged.connect(self.queryChanged.emit)
        layout.addWidget(self.search)
        for control in controls:
            layout.addWidget(control)
        layout.addWidget(content, 1)
        self._resize_cards()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_cards()

    def _resize_cards(self):
        for view in self.list_views:
            view.setViewMode(QListView.IconMode)
            # IconMode defaults to a vertical flow in some Qt bindings, which
            # produces one item per row in the narrow editor dock.
            view.setFlow(QListView.LeftToRight)
            view.setResizeMode(QListView.Adjust)
            view.setWrapping(True)
            view.setSpacing(4)
            available = max(180, view.viewport().width())
            card_width = max(82, (available - 8) // 2)
            view.setGridSize(QSize(card_width, 104))
            view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

class CategoryPage(BrowserPage):
    """Browser page that owns one or more category content widgets."""

    def __init__(self, translate, categories, contents, filters, list_views, parent=None):
        self.filters = filters
        body = QWidget(parent)
        body.setObjectName("editorCategoryBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(8)
        category_bar = QWidget(body)
        category_bar.setObjectName("editorCategoryBar")
        category_layout = QHBoxLayout(category_bar)
        category_layout.setContentsMargins(0, 0, 0, 0)
        category_layout.setSpacing(6)
        self.category_group = QButtonGroup(category_bar)
        self.category_group.setExclusive(True)
        self.category_buttons = {}

        self.content_stack = QStackedWidget(body)
        self.content_stack.setObjectName("editorElementsStack")
        for key, label in categories:
            button = QToolButton(category_bar)
            button.setObjectName("editorCategoryButton")
            button.setText(label)
            button.setCheckable(True)
            button.setAccessibleName(label)
            button.clicked.connect(lambda _checked=False, k=key: self.set_category(k))
            self.category_group.addButton(button)
            self.category_buttons[key] = button
            category_layout.addWidget(button)
            self.content_stack.addWidget(contents[key])

        body_layout.addWidget(category_bar)
        body_layout.addWidget(self.content_stack, 1)
        super().__init__(translate("Search"), body, parent, list_views)
        self.active_category = categories[0][0]
        self.category_buttons[self.active_category].setChecked(True)

    def set_category(self, category):
        if category not in self.category_buttons:
            return
        self.active_category = category
        self.category_buttons[category].setChecked(True)
        self.content_stack.setCurrentIndex(list(self.category_buttons).index(category))
        self.apply_filter(self.search.text())
        self._resize_cards()

    def apply_filter(self, query):
        self.filters[self.active_category].setText(query)

class AssetsPage(BrowserPage):
    """Media/assets browser without an unnecessary category selector."""

    def __init__(self, translate, contents, filters, list_views, import_action=None, parent=None):
        self.import_button = QPushButton(translate("Import File"))
        self.import_button.setObjectName("editorImportButton")
        self.import_button.setToolTip(translate("Import video, audio, or image files"))
        self.import_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.import_button.setMinimumHeight(34)
        if import_action is not None:
            self.import_button.clicked.connect(
                lambda _checked=False: import_action.trigger())
        super().__init__(
            translate("Search assets"),
            contents["media"],
            parent,
            list_views,
            controls=(self.import_button,),
        )
        self.media_filter = filters["media"]
        self.queryChanged.connect(self.media_filter.setText)


class ElementsPage(CategoryPage):
    """Transitions and emojis browser, separate from imported media."""

    def __init__(self, translate, contents, filters, list_views, parent=None):
        super().__init__(
            translate,
            (
                ("transitions", translate("Transitions")),
                ("emojis", translate("Emojis")),
            ),
            contents,
            filters,
            list_views,
            parent,
        )

class EditorPanel(QWidget):
    """Persistent navigation rail and state-driven contextual editor panel."""

    activeSectionChanged = pyqtSignal(str)

    def __init__(self, window, settings, translate, contents, filters, list_views, parent=None):
        super().__init__(parent)
        self.setObjectName("editorPanel")
        self.window = window
        self.settings = settings
        self.translate = translate
        self.queries = {section: "" for section in EditorSection.ALL}
        self.pages = {}
        self.active_section = None

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_rail())

        self.context = QFrame(self)
        self.context.setObjectName("editorContextPanel")
        context_layout = QVBoxLayout(self.context)
        context_layout.setContentsMargins(0, 0, 0, 0)
        context_layout.setSpacing(8)

        header = QWidget(self.context)
        header.setObjectName("editorContextHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 12, 10, 0)
        self.tool_back = QToolButton(header)
        self.tool_back.setObjectName("editorToolBackButton")
        self.tool_back.setText("<")
        self.tool_back.setToolTip(translate("Back to tools"))
        self.tool_back.setAccessibleName(translate("Back to tools"))
        self.tool_back.setVisible(False)
        self.tool_back.clicked.connect(self._close_youtube_embed)
        header_layout.addWidget(self.tool_back)
        self.title = QLabel(header)
        self.title.setObjectName("editorContextTitle")
        header_layout.addWidget(self.title, 1)
        collapse = QToolButton(header)
        collapse.setObjectName("editorCollapseButton")
        collapse.setText("<")
        collapse.setToolTip(translate("Collapse panel"))
        collapse.setAccessibleName(translate("Collapse panel"))
        collapse.clicked.connect(self.collapse_context)
        header_layout.addWidget(collapse)
        context_layout.addWidget(header)

        self.stack = QStackedWidget(self.context)
        self.stack.setObjectName("editorSectionStack")
        context_layout.addWidget(self.stack, 1)
        root.addWidget(self.context, 1)

        elements = ElementsPage(
            translate,
            {
                "transitions": contents["transitions"],
                "emojis": contents["emojis"],
            },
            {
                "transitions": filters["transitions"],
                "emojis": filters["emojis"],
            },
            (list_views["transitions"], list_views["emojis"]),
            self.stack,
        )

        assets = AssetsPage(
            translate,
                         {"media": contents["elements"]},
                         {"media": filters["elements"]},
                         (list_views["elements"],),
                         getattr(window, "actionImportFiles", None),
                         self.stack,
        )
        effects = BrowserPage(
            translate("Search effects"), contents["effects"], self.stack,
            (list_views["effects"],),
        )
        properties = self._build_properties_page(contents["properties"], filters["properties"])
        tools = self.from AnyQt.QtCore import QObject, QCoreApplicationols_page()

        for section, page in (
                (EditorSection.ELEMENTS, elements),
                (EditorSection.ASSETS, assets),
                (EditorSection.EFFECTS, effects),
                (EditorSection.TOOLS, tools),
                (EditorSection.PROPERTIES, properties)):
            self.pages[section] = page
            self.stack.addWidget(page)
            if hasattr(page, "queryChanged"):
                page.queryChanged.connect(
                    lambda query, current=section: self._query_changed(current, query))

        self._search_handlers = {
            EditorSection.ELEMENTS: elements.apply_filter,
            EditorSection.ASSETS: assets.media_filter.setText,
            EditorSection.EFFECTS: filters["effects"].setText,
            EditorSection.TOOLS: tools.card_grid.set_filter,
            EditorSection.PROPERTIES: self._filter_properties,
        }

        initial = settings.get("editor_active_section") or EditorSection.ELEMENTS
        self.set_active_section(initial)

    def _build_rail(self):
        rail = QFrame(self)
        rail.setObjectName("editorSectionRail")
        rail.setFixedWidth(78)
        layout = QVBoxLayout(rail)
        layout.setContentsMargins(6, 10, 6, 10)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignTop)
        self.section_group = QButtonGroup(rail)
        self.section_group.setExclusive(True)
        self.section_buttons = {}
        items = (
            (EditorSection.ASSETS, self.translate("Assets"), "tool-import-files.svg"),
            (EditorSection.ELEMENTS, self.translate("Elements"), "tool-import-files.svg"),
            (EditorSection.EFFECTS, self.translate("Effects"), "view-analysis.svg"),
            (EditorSection.TOOLS, self.translate("Tools"), "tool-timing.svg"),
            (EditorSection.PROPERTIES, self.translate("Properties"), "view-color.svg"),
        )
        for section, label, icon_name in items:
            button = QToolButton(rail)
            button.setObjectName("editorSectionButton")
            button.setText(label)
            button.setIcon(_bento_icon(icon_name))
            button.setIconSize(QSize(22, 22))
            button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            button.setCheckable(True)
            button.setAccessibleName(label)
            button.setMinimumHeight(62)
            button.setMinimumWidth(62)
            button.clicked.connect(
                lambda _checked=False, value=section: self.set_active_section(value))
            self.section_group.addButton(button)
            self.section_buttons[section] = button
            layout.addWidget(button)
        layout.addStretch(1)
        return rail

    def _build_tools_page(self):
        grid = CardGrid(self.stack, columns=1)
        actions = (
            (self.translate("Import Media"), self.translate("Add video, audio, or images"),
             "tool-import-files.svg", "actionImportFiles"),
            (self.translate("Create Title"), self.translate("Create a static title"),
             "ai-action-captions.svg", "actionTitle"),
            (self.translate("Animated Title"), self.translate("Create an animated title"),
             "ai-action-create-video.svg", "actionAnimatedTitle"),
            (self.translate("Generate"), self.translate("Open generative media tools"),
             "tool-generate-sparkle.svg", "actionGenerate"),
        )
        for title, description, icon_name, action_name in actions:
            grid.add_card(
                title, description, _bento_icon(icon_name),
                lambda name=action_name: self._trigger_action(name),
            )
        grid.add_card(
            self.translate("YouTube Embed"),
            self.translate("Search and add videos from YouTube"),
            _bento_icon("tool-import-files.svg"),
            self._open_youtube_embed,
        )
        main_page = BrowserPage(self.translate("Search tools"), grid, self.stack)
        main_page.card_grid = grid
        youtube_page = YoutubeEmbedPage(self.translate, self.window, self.stack)
        page = QWidget(self.stack)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(main_page)
        page_layout.addWidget(youtube_page)
        youtube_page.hide()
        page.card_grid = grid
        page.search = main_page.search
        page.tools_main_page = main_page
        page.youtube_page = youtube_page
        return page

    def _open_youtube_embed(self):
        page = self.pages[EditorSection.TOOLS]
        page.tools_main_page.hide()
        page.youtube_page.show()
        self.tool_back.show()
        self.title.setText(self.translate("YouTube Embed"))

    def _close_youtube_embed(self):
        page = self.pages[EditorSection.TOOLS]
        page.youtube_page.hide()
        page.tools_main_page.show()
        self.tool_back.hide()
        self.title.setText(self.translate("Tools"))

    def _build_properties_page(self, properties_content, properties_filter):
        properties_filter.clear()
        properties_filter.hide()

        page = QWidget(self.stack)
        page.setObjectName("editorPropertiesBody")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(properties_content, 1)
        page.properties_filter = properties_filter
        return page

    def _trigger_action(self, action_name):
        action = getattr(self.window, action_name, None)
        if action and action.isEnabled():
            action.trigger()

    def _filter_properties(self, query):
        page = self.pages[EditorSection.PROPERTIES]
        page.properties_filter.setText(query)

    def _query_changed(self, section, query):
        self.queries[section] = query
        if section == self.active_section:
            self._search_handlers[section](query)

    def set_active_section(self, section):
        if section not in EditorSection.ALL:
            section = EditorSection.ELEMENTS
        changed = section != self.active_section
        self.active_section = section
        self.section_buttons[section].setChecked(True)
        self.stack.setCurrentWidget(self.pages[section])
        self.title.setText(self.section_buttons[section].text())
        self.context.show()
        page = self.pages[section]
        if hasattr(page, "search") and page.search.text() != self.queries[section]:
            page.search.setText(self.queries[section])
        self._search_handlers[section](self.queries[section])
        self.settings.set("editor_active_section", section)
        if changed:
            self.activeSectionChanged.emit(section)

    def collapse_context(self):
        self.context.hide()
