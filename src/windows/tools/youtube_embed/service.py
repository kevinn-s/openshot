"""Network and metadata services used by the YouTube Embed tool."""

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SUGGEST_URL = "https://clients1.google.com/complete/search"


def get_suggestions(query, language="en", timeout=8):
    """Return autocomplete terms from YouTube's undocumented suggestion endpoint."""
    query = str(query or "").strip()
    if not query:
        return []

    params = urlencode({
        "client": "youtube",
        "ds": "yt",
        "hl": language,
        "q": query,
        "callback": "google.sbox.p50",
    })
    request = Request(
        "%s?%s" % (SUGGEST_URL, params),
        headers={"User-Agent": "OpenShot Video Editor"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload = response.read().decode("utf-8")

    start = payload.find("(")
    end = payload.rfind(")")
    if start < 0 or end <= start:
        raise ValueError("Unexpected YouTube suggestion response")
    data = json.loads(payload[start + 1:end])
    return [str(item[0]) for item in data[1] if item and item[0]]


def search_videos(query, limit=10):
    """Search YouTube with yt-dlp and return UI-friendly video dictionaries."""
    import yt_dlp

    query = str(query or "").strip()
    if not query:
        return []

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": True,
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info("ytsearch%d:%s" % (int(limit), query), download=False)

    results = []
    for entry in (info or {}).get("entries", []) or []:
        if not entry:
            continue
        results.append({
            "id": entry.get("id", ""),
            "title": entry.get("title", ""),
            "channel": entry.get("channel") or entry.get("uploader") or "",
            "duration": entry.get("duration_string") or _format_duration(entry.get("duration")),
            "thumbnail": entry.get("thumbnail", ""),
            "url": entry.get("webpage_url") or entry.get("url", ""),
        })
    return results


def get_thumbnail(url, timeout=8):
    """Fetch a result thumbnail for display in the tool panel."""
    if not url:
        return b""
    request = Request(str(url), headers={"User-Agent": "OpenShot Video Editor"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _format_duration(seconds):
    if seconds is None:
        return ""
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return "%d:%02d:%02d" % (hours, minutes, seconds)
    return "%d:%02d" % (minutes, seconds)
