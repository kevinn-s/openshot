class ToolsPanel(QWidget):
    """Owns the tool browser, persistent tools, and local navigation."""

    activeToolChanged = pyqtSignal(object, object)
    navigationChanged = pyqtSignal(str, bool)
    queryChanged = pyqtSignal(str)

    ANIMATION_DURATION = 250

    def __init__(
        self,
        editor,
        settings,
        translate=str,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("editorToolsPanel")

        self.editor = editor
        self.settings = settings
        self.translate = translate

        self.tools = {}
        self._active_tool_id = None
        self._transitioning = False
        self._animation = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.stack = QStackedWidget(self)
        self.stack.setObjectName("editorToolsStack")
        layout.addWidget(self.stack)

        self.browser = ToolBrowserPage(translate, self.stack)
        self.browser.queryChanged.connect(self.queryChanged.emit)
        self.stack.addWidget(self.browser)

        # Compatibility with EditorPanel's existing search contract.
        self.search = self.browser.search
        self.card_grid = self.browser.card_grid

        self._add_action_cards()
        self._create_registered_tools()
        self._restore_active_tool()

    @property
    def active_tool_id(self):
        return self._active_tool_id

    @property
    def active_tool(self):
        if self._active_tool_id is None:
            return None
        return self.tools.get(self._active_tool_id)

    @property
    def navigation_title(self):
        tool = self.active_tool
        if tool is None:
            return self.translate("Tools")
        return self.translate(tool.name)

    @property
    def can_go_back(self):
        return self.active_tool is not None

    def set_filter(self, query):
        self.card_grid.set_filter(query)

    def set_active_tool(self, tool_id, animate=True):
        if tool_id is None:
            return self.close_tool(animate=animate)
        return self.open_tool(tool_id, animate=animate)

    def open_tool(self, tool_id, animate=True):
        if self._transitioning:
            return False

        if tool_id not in self.tools:
            raise KeyError("Unknown tool: %s" % tool_id)

        next_tool = self.tools[tool_id]
        previous_tool = self.active_tool

        if previous_tool is next_tool:
            return False

        # A direct tool-to-tool transition is supported even though the current
        # UI normally returns to the browser first.
        if previous_tool is not None:
            previous_tool.deactivate()

        try:
            next_tool.activate()
        except Exception:
            if previous_tool is not None:
                previous_tool.activate()
            raise

        self._active_tool_id = tool_id
        self._save_active_tool()

        self.navigationChanged.emit(
            self.translate(next_tool.name),
            True,
        )

        def completed():
            self.activeToolChanged.emit(previous_tool, next_tool)

        self._slide_to(
            next_tool,
            direction=1,
            animate=animate,
            completed=completed,
        )
        return True

    def close_tool(self, animate=True):
        if self._transitioning:
            return False

        previous_tool = self.active_tool
        if previous_tool is None:
            return False

        previous_tool.deactivate()
        self._active_tool_id = None
        self._save_active_tool()

        self.navigationChanged.emit(
            self.translate("Tools"),
            False,
        )

        def completed():
            self.activeToolChanged.emit(previous_tool, None)

        self._slide_to(
            self.browser,
            direction=-1,
            animate=animate,
            completed=completed,
        )
        return True

    def _slide_to(self, next_widget, direction, animate, completed):
        """Slide forward from the right or backward from the left."""

        current_widget = self.stack.currentWidget()

        if current_widget is next_widget:
            completed()
            return

        width = self.stack.width()
        height = self.stack.height()

        if (
            not animate
            or not self.isVisible()
            or width <= 0
            or height <= 0
        ):
            self.stack.setCurrentWidget(next_widget)
            current_widget.move(0, 0)
            next_widget.move(0, 0)
            completed()
            return

        self._transitioning = True

        current_widget.setGeometry(0, 0, width, height)
        current_widget.move(0, 0)

        next_widget.setGeometry(0, 0, width, height)
        next_widget.move(direction * width, 0)
        next_widget.show()
        next_widget.raise_()

        current_animation = QPropertyAnimation(
            current_widget,
            b"pos",
            self,
        )
        current_animation.setDuration(self.ANIMATION_DURATION)
        current_animation.setStartValue(QPoint(0, 0))
        current_animation.setEndValue(
            QPoint(-direction * width, 0)
        )
        current_animation.setEasingCurve(_out_cubic())

        next_animation = QPropertyAnimation(
            next_widget,
            b"pos",
            self,
        )
        next_animation.setDuration(self.ANIMATION_DURATION)
        next_animation.setStartValue(
            QPoint(direction * width, 0)
        )
        next_animation.setEndValue(QPoint(0, 0))
        next_animation.setEasingCurve(_out_cubic())

        group = QParallelAnimationGroup(self)
        group.addAnimation(current_animation)
        group.addAnimation(next_animation)
        self._animation = group

        def finish_transition():
            self.stack.setCurrentWidget(next_widget)
            current_widget.move(0, 0)
            next_widget.move(0, 0)

            self._transitioning = False
            self._animation = None
            group.deleteLater()

            completed()

        group.finished.connect(finish_transition)
        group.start()

    def _add_action_cards(self):
        actions = (
            (
                self.translate("Import Media"),
                self.translate("Add video, audio, or images"),
                "tool-import-files.svg",
                "actionImportFiles",
            ),
            (
                self.translate("Create Title"),
                self.translate("Create a static title"),
                "ai-action-captions.svg",
                "actionTitle",
            ),
            (
                self.translate("Animated Title"),
                self.translate("Create an animated title"),
                "ai-action-create-video.svg",
                "actionAnimatedTitle",
            ),
            (
                self.translate("Generate"),
                self.translate("Open generative media tools"),
                "tool-generate-sparkle.svg",
                "actionGenerate",
            ),
        )

        for title, description, icon_name, action_name in actions:
            action = getattr(self.editor, action_name, None)
            card = self.card_grid.add_card(
                title,
                description,
                _tool_icon(icon_name),
                lambda name=action_name: self._trigger_action(name),
            )

            card.setEnabled(
                action is not None and action.isEnabled()
            )

            if action is not None:
                action.changed.connect(
                    lambda card=card, action=action:
                    card.setEnabled(action.isEnabled())
                )

    def _create_registered_tools(self):
        for tool_id, tool_class in ToolRegistry.all().items():
            tool = tool_class(
                self.editor,
                self.translate,
                self.stack,
            )

            self.tools[tool_id] = tool
            self.stack.addWidget(tool)

            self.card_grid.add_card(
                self.translate(tool.name),
                self.translate(tool.description or ""),
                _tool_icon(tool.icon),
                lambda tool_id=tool_id: self.open_tool(tool_id),
            )

    def _trigger_action(self, action_name):
        action = getattr(self.editor, action_name, None)
        if action is not None and action.isEnabled():
            action.trigger()

    def _restore_active_tool(self):
        tool_id = self.settings.get("editor_active_tool")

        if tool_id in self.tools:
            self.open_tool(tool_id, animate=False)
            return

        # Invalid values from an older installation must not leave the panel
        # with an active ID that does not have a corresponding widget.
        self._active_tool_id = None
        self.stack.setCurrentWidget(self.browser)
        self._save_active_tool()

    def _save_active_tool(self):
        self.settings.set(
            "editor_active_tool",
            self._active_tool_id or "",
        )
