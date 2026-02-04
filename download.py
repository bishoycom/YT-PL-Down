"""Simple YouTube playlist downloader using yt-dlp.

Usage: python download.py <PLAYLIST_URL> [--audio] [--outdir DIR]
"""

from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

import yt_dlp
from rich.console import Console

console = Console()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download YouTube playlists or single videos using yt-dlp")
    p.add_argument("url", nargs="?", help="YouTube playlist or video URL (optional; you'll be prompted if omitted)")
    p.add_argument("--outdir", default="downloads", help="Output directory")
    p.add_argument("--audio", action="store_true", help="Download audio only (convert to mp3, requires ffmpeg)")
    p.add_argument("--format", default="best", help="Format selector (yt-dlp format string). Default: best")
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

    def __call__(self, d: dict):
        status = d.get("status")
        if status == "downloading":
            downloaded = d.get("downloaded_bytes")
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            speed = d.get("speed")
            percent = None
            if downloaded and total:
                percent = downloaded / total * 100
            msg = f"[downloading] {d.get('filename', '')}"
            if percent is not None:
                msg += f" — {percent:5.1f}%"
            if speed:
                msg += f" @ {yt_dlp.utils.format_bytes(speed)}/s"
            console.print(msg)
        elif status == "finished":
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
    }

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
        if args.format and args.format != "best":
            ydl_opts["format"] = args.format

    console.print(f"Starting download into: [bold green]{outdir}[/]")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([args.url])
    except Exception as e:
        console.print(f"[red]Download failed:[/] {e}")
        return 1

    console.print(":white_check_mark: Done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
