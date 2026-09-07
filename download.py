"""Simple YouTube playlist downloader using yt-dlp.

Usage: python download.py <PLAYLIST_URL> [--audio] [--outdir DIR]
"""

from __future__ import annotations
import argparse
import shutil
import sys
import time
from pathlib import Path

import yt_dlp
from rich.console import Console


# Windows may inherit a legacy console code page that cannot represent Arabic
# titles or YouTube's Unicode separators. Keep progress reporting from aborting
# an otherwise valid download.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

console = Console()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download YouTube playlists or single videos using yt-dlp")
    p.add_argument("url", nargs="?", help="YouTube playlist or video URL (optional; you'll be prompted if omitted)")
    p.add_argument("--outdir", default="downloads", help="Output directory")
    p.add_argument("--audio", action="store_true", help="Download audio only (convert to mp3, requires ffmpeg)")
    p.add_argument(
        "--format",
        default="bestvideo[height<=360][vcodec^=avc1]+bestaudio[ext=m4a]/best[height<=360]",
        help="Format selector (yt-dlp format string). Default: compatible 360p MP4",
    )
    p.add_argument("--concurrent-fragments", type=int, default=1, help="Parallel fragments per video (advanced)")
    args, unknown = p.parse_known_args()
    if unknown:
        console.print(f"[yellow]Warning: ignoring unknown arguments: {unknown}[/]")
    if not args.url:
        try:
            args.url = input("Enter YouTube playlist or video URL: ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("[red]No URL provided. Aborting.[/]")
            args.url = None
        if not args.url:
            console.print("[red]No URL provided. Aborting.[/]")
            args.url = None
    return args


class ProgressHook:
    def __init__(self):
        self.current = None
        self.finished = set()
        self.last_update = 0.0

    def __call__(self, d: dict):
        status = d.get("status")
        if status == "downloading":
            filename = d.get("filename", "")
            now = time.monotonic()
            if filename != self.current:
                self.current = filename
                self.last_update = 0.0
            if now - self.last_update < 2:
                return
            self.last_update = now
            downloaded = d.get("downloaded_bytes")
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            speed = d.get("speed")
            percent = None
            if downloaded and total:
                percent = downloaded / total * 100
            msg = f"[downloading] {filename}"
            if percent is not None:
                msg += f" — {percent:5.1f}%"
            if speed:
                msg += f" @ {yt_dlp.utils.format_bytes(speed)}/s"
            console.print(msg)
        elif status == "finished":
            info = d.get("info_dict") or {}
            self.finished.add(info.get("id") or d.get("filename"))
            console.print(f"[finished] {d.get('filename')}")
        elif status == "error":
            console.print(f"[error] {d}")


def main() -> int:
    args = parse_args()
    if not args.url:
        console.print("[red]No URL provided. Exiting.[/]")
        return 2
    outdir = Path(args.outdir).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    hook = ProgressHook()

    ydl_opts = {
        "outtmpl": str(outdir / "%(playlist_index)s - %(title)s.%(ext)s"),
        "ignoreerrors": True,
        "continuedl": True,
        "noplaylist": False,
        "progress_hooks": [hook],
        "concurrent_fragment_downloads": args.concurrent_fragments,
        "noprogress": True,
        # Short ranged requests are much more resilient to YouTube/CDN
        # throttling and connection resets than one long HTTP transfer.
        "http_chunk_size": 10 * 1024 * 1024,
        "retries": 20,
        "fragment_retries": 20,
        "file_access_retries": 3,
        # Recent YouTube players require their JavaScript challenges to be
        # evaluated before usable media formats are exposed.
        "js_runtimes": {"deno": {}},
        "remote_components": {"ejs:github"},
    }

    if aria2_path := shutil.which("aria2c"):
        ydl_opts.update({
            "external_downloader": {"default": aria2_path},
            "external_downloader_args": {
                "aria2c": [
                    "-x", "8", "-s", "8", "-k", "1M",
                    "--disable-ipv6=true",
                    "--max-tries=20",
                    "--retry-wait=2",
                    "--connect-timeout=30",
                    "--timeout=30",
                    "--file-allocation=none",
                ],
            },
        })
        console.print("Using aria2c with 8 connections per stream")

    if args.audio:
        # Extract audio with ffmpeg
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        })
    else:
        if args.format:
            ydl_opts["format"] = args.format

    console.print(f"Starting download into: [bold green]{outdir}[/]")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([args.url])
    except Exception as e:
        console.print(f"[red]Download failed:[/] {e}")
        return 1

    if result:
        console.print(
            f"[red]Download completed with errors.[/] "
            f"Successfully downloaded {len(hook.finished)} video(s)."
        )
        return result

    console.print(f":white_check_mark: Done - downloaded {len(hook.finished)} video(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
