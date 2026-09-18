
from typing import Optional, Dict, Any, List, Tuple, Iterable, Union
from enum import IntEnum

from qt_api import QObject, QWidget
from qt_api import pyqtSignal as Signal, pyqtProperty as Property

from windows.tools.editor_tool import ToolRegistry, EditorTool

class ToolStatus(IntEnum):
    NoState = 0

    Idle = 1

    Running = 2

    Pending = 3

    Error = 4

class ToolsPanel(QWidget):
    def __init__(self, registry, parent=None,
                 properties=None):

        self.__active_tool_id = None #type: Optional[str]
        self.__tool_registy = ToolRegistry() #type: ToolRegistry

    active_tool = Signal(Optional[str])

    def set_active_tool(self, id):
        if self.__active_tool_id != id:
            self.__active_tool_id = id
            self.active_tool.emit(id)

    def close_active_tool(self):
        if self.__active_tool_id != None:
            self.__active_tool_id = None
            self.active_tool.emit(None)

    def _tool(self, id: str) -> Optional[EditorTool]:
        if id is None:
            return None

        return

