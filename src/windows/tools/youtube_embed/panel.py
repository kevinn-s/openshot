"""YouTube search page embedded in the editor Tools panel."""

from qt_api import Qt, QLineEdit, QPixmap, QThread, QTimer, pyqtSignal
from qt_api import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QVBoxLayout,
    QScrollArea, QWidget,
)

from . import service


class _RequestThread(QThread):
    suggestionsReady = pyqtSignal(str, list)
    resultsReady = pyqtSignal(str, list)
    failed = pyqtSignal(str, str)

    def __init__(self, query, mode, parent=None):
        super().__init__(parent)
        self.query = query
        self.mode = mode

    def run(self):
        try:
            if self.mode == "suggestions":
                values = service.get_suggestions(self.query)
                self.suggestionsReady.emit(self.query, values)
            elif self.mode == "results":
                values = service.search_videos(self.query)
                for video in values:
                    try:
                        video["thumbnail_data"] = service.get_thumbnail(video.get("thumbnail"))
                    except Exception:
                        video["thumbnail_data"] = b""
                self.resultsReady.emit(self.query, values)
        except Exception as exc:
            self.failed.emit(self.mode, str(exc))


class VideoResultCard(QFrame):
    clicked = pyqtSignal(dict)

    def __init__(self, video, parent=None):
        super().__init__(parent)
        self.video = video
        self.setObjectName("youtubeResultCard")
        self.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(4)

        thumbnail = QLabel(self)
        thumbnail.setObjectName("youtubeResultThumbnail")
        thumbnail.setMinimumHeight(118)
        thumbnail.setAlignment(Qt.AlignCenter)
        thumbnail.setText("YouTube")
        thumbnail_data = video.get("thumbnail_data")
        if thumbnail_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(thumbnail_data):
                thumbnail.setPixmap(pixmap.scaled(
                    320, 180, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                thumbnail.setText("")
        layout.addWidget(thumbnail)

        title = QLabel(str(video.get("title", "")), self)
        title.setObjectName("youtubeResultTitle")
        title.setWordWrap(True)
        layout.addWidget(title)
        channel = QLabel(str(video.get("channel", "")), self)
        channel.setObjectName("youtubeResultChannel")
        layout.addWidget(channel)

        duration = video.get("duration")
        if duration:
            duration_label = QLabel(str(duration), self)
            duration_label.setObjectName("youtubeResultDuration")
            layout.addWidget(duration_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.video)
        super().mousePressEvent(event)


class YoutubeEmbedPage(QWidget):
    """Search-only first version of the in-panel YouTube Embed tool."""

    def __init__(self, translate=str, window=None, parent=None):
        super().__init__(parent)
        self.translate = translate
        self.setObjectName("youtubeEmbedPage")
        self._request_threads = []
        self._last_query = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 12)
        layout.setSpacing(8)

        self.search = SearchField(translate("Search from YouTube"), self)
        layout.addWidget(self.search)

        self.suggestions = QListWidget(self)
        self.suggestions.setObjectName("youtubeSuggestions")
        self.suggestions.setVisible(False)
        self.suggestions.setMaximumHeight(180)
        self.suggestions.itemClicked.connect(self._suggestion_clicked)
        layout.addWidget(self.suggestions)

        self.status = QLabel(translate("Search to find content"), self)
        self.status.setObjectName("youtubeEmptyState")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.results = QWidget(self)
        self.results.setObjectName("youtubeResults")
        self.results_layout = QVBoxLayout(self.results)
        self.results_layout.setContentsMargins(0, 0, 0, 0)
        self.results_layout.setSpacing(12)

        # Keep a long result set inside the tool dock instead of expanding its
        # minimum height and pushing the timeline out of the workspace.
        self.results_scroll = QScrollArea(self)
        self.results_scroll.setObjectName("youtubeResultsScroll")
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setFrameShape(QFrame.NoFrame)
        self.results_scroll.setWidget(self.results)
        layout.addWidget(self.results_scroll, 1)


        self._suggestion_query = ""
        self._suggestion_timer = QTimer(self)
        self._suggestion_timer.setSingleShot(True)
        self._suggestion_timer.setInterval(250)
        self._suggestion_timer.timeout.connect(self._request_suggestions)
        self.search.textChanged.connect(self._search_text_changed)
        self.search.submitted.connect(self.submit_search)

    def _search_text_changed(self, text):
        query = text.strip()
        self.suggestions.clear()
        self.suggestions.setVisible(bool(query))
        if not query:
            self.status.setText(self.translate("Search to find content"))
            return
        self._suggestion_query = query
        self._suggestion_timer.start()

    def _request_suggestions(self):
        query = self._suggestion_query
        if query and query == self.search.text().strip():
            self._start_request(query, "suggestions")

    def submit_search(self):
        query = self.search.text().strip()
        if not query:
            return
        self._last_query = query
        self.suggestions.setVisible(False)
        self.status.setText(self.translate("Searching YouTube..."))
        self._clear_results()
        self._start_request(query, "results")

    def _suggestion_clicked(self, item):
        self.search.setText(item.text())
        self.submit_search()

    def _start_request(self, query, mode):
        thread = _RequestThread(query, mode, self)
        thread.suggestionsReady.connect(self._suggestions_ready)
        thread.resultsReady.connect(self._results_ready)
        thread.failed.connect(self._request_failed)
        thread.finished.connect(lambda t=thread: self._thread_finished(t))
        self._request_threads.append(thread)
        thread.start()

    def _suggestions_ready(self, query, values):
        if query != self.search.text().strip():
            return
        self.suggestions.clear()
        for value in values[:8]:
            QListWidgetItem(value, self.suggestions)
        self.suggestions.setVisible(bool(values))

    def _results_ready(self, query, values):
        if query != self._last_query:
            return
        self._clear_results()
        if not values:
            self.status.setText(self.translate("No videos found"))
            return
        self.status.clear()
        self.status.hide()
        for video in values:
            card = VideoResultCard(video, self.results)
            self.results_layout.addWidget(card)
        self.results_layout.addStretch(1)

    def _request_failed(self, mode, message):
        if mode == "results":
            self.status.setText(self.translate("Unable to search YouTube: %s") % message)

    def _thread_finished(self, thread):
        if thread in self._request_threads:
            self._request_threads.remove(thread)
        thread.deleteLater()

    def _clear_results(self):
        self.status.show()
        while self.results_layout.count():
            item = self.results_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()



class SearchField(QFrame):
    """Compact search surface used by the YouTube tool."""

    textChanged = pyqtSignal(str)
    submitted = pyqtSignal()

    def __init__(self, placeholder, parent=None):
        super().__init__(parent)
        self.setObjectName("youtubeSearchField")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 8, 0)
        self.input = QLineEdit(self)
        self.input.setObjectName("youtubeSearchInput")
        self.input.setPlaceholderText(placeholder)
        self.input.setClearButtonEnabled(True)
        layout.addWidget(self.input)
        self.input.textChanged.connect(self.textChanged.emit)
        self.input.returnPressed.connect(self.submitted.emit)

    def text(self):
        return self.input.text()

    def setText(self, text):
        self.input.setText(text)
