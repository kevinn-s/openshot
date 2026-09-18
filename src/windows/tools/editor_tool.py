from qt_api import Qt, QLineEdit, QPixmap, QThread, QTimer, pyqtSignal
from qt_api import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QVBoxLayout,
    QWidget
)

class EditorTool(QWidget):
    state_changed = pyqtSignal()

    id: str
    name: str
    description: str | None = None
    category: str = "General"
    icon: str | None = None

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
    def activate(self):
        pass
    def deactivate(self):
        pass

class ToolRegistry:
    _tools: dict[str, type[EditorTool]] = {}

    @classmethod
    def register(cls, tool_class: type[EditorTool]):
        if not issubclass(tool_class, EditorTool):
            raise TypeError(
                f"{tool_class.__name__} must inherit EditorTool"
            )

        tool_id = getattr(tool_class, "id", None)
        tool_name = getattr(tool_class, "name", None)

        if not tool_id:
            raise ValueError(
                f"{tool_class.__name__} must define 'id'"
            )
        if not tool_name:
            raise ValueError(
                f"{tool_class.__name__} must define 'name'"
            )
        if tool_id in cls._tools:
            raise ValueError(
                f"Tool '{tool_id}' is already registered"
            )

        cls._tools[tool_id] = tool_class
        return tool_class

def register_tool(cls):
    return ToolRegistry.register(cls)
