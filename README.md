# YT-Downloader ✅

A small Python CLI to download YouTube playlists using `yt-dlp` (robust and actively maintained).

## Features

- Download entire playlists or single videos
- Save video or **audio-only** (MP3 using ffmpeg)
- Resume interrupted downloads
- Simple, cross-platform CLI runnable in VS Code

## Requirements

- Python 3.10+ (3.11 recommended)
- `ffmpeg` installed and available on PATH (only required for audio conversion)

## Install

1. Create a virtual environment (recommended):

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # Windows PowerShell
# or .venv\Scripts\activate      # cmd.exe
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Basic usage

```bash
python download.py "<PLAYLIST_URL>" --outdir "downloads"         # download videos
python download.py "<PLAYLIST_URL>" --audio --outdir "audio"     # download audio (mp3)
```

Run `python download.py -h` for all options.

## Notes

- `yt-dlp` is recommended over `pytube` for reliability with playlists and newer YouTube changes.
- If you plan to convert to MP3, ensure `ffmpeg` is installed and on your PATH.
- The default video format is a compatible 360p MP4. Pass a custom `--format` selector if you need another quality.
- If `aria2c` is installed, the downloader automatically uses eight connections per stream for faster, more resilient transfers.

### Installing ffmpeg (Windows) ✅

- Recommended: install via winget:

```powershell
winget install -e --id Gyan.FFmpeg
```

- After installation the PATH is updated for new shells; **restart your terminal** (or sign out/in) so `ffmpeg` is available in your current session.

- Quick remux (fix container/timestamps) example using `ffmpeg` (PowerShell):

```powershell
# creates a fixed copy for each .mp4 in downloads
Get-ChildItem .\downloads -Filter *.mp4 | ForEach-Object {
  $in = $_.FullName
  $out = Join-Path $_.DirectoryName ($_.BaseName + ".fixed.mp4")
  ffmpeg -i $in -c copy $out
}
```

### JS runtime / EJS challenges

- Some YouTube videos require a JavaScript runtime and the EJS challenge solver to extract formats reliably. Install **Deno**; the downloader enables Deno and the EJS component automatically.
- Keep the dependencies current with `python -m pip install --upgrade -r requirements.txt` when YouTube extraction stops working.

---

License: MIT
