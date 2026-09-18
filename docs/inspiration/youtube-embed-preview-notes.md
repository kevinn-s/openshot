# YouTube Embed Preview Notes

This document preserves the experimental preview implementation for future
reference. It is not currently part of the active YouTube Embed tool.

## Architecture

- Download a temporary preview with `yt-dlp`.
- Prefer H.264/AVC video and AAC audio for libopenshot compatibility.
- Validate the completed file with FFmpeg and `ffprobe`.
- Load the file through OpenShot's existing `MainWindow.LoadFilePreviewSignal`.
- Use the existing main `VideoWidget` and preview thread rather than creating a
  second renderer.
- Add an overlay containing play/pause, timecode, and a dual-handle in/out
  range slider.
- Restore the timeline with `MainWindow.LoadFileSignal("")` when leaving preview.

## Important Lessons

- The OpenShot preview widget is created after the editor panel, so an overlay
  must attach lazily when a video is selected.
- A refresh must not emit `LoadFileSignal("")` while the player is in file
  preview mode, or the selected file is immediately replaced by the timeline.
- Temporary downloads should use unique directories and must not resume or
  reuse incomplete files.
- FFmpeg decoding validation should happen before handing media to libopenshot.
- `LoadFilePreviewSignal` switches readers asynchronously, so initial seek and
  playback should be deferred until the reader switch has completed.

## Future Work

- Move the range control onto the main video preview.
- Download only the selected range with `yt-dlp` and FFmpeg.
- Import the resulting local media through `FilesModel.process_urls()`.
- Add cancellation and progress reporting.
