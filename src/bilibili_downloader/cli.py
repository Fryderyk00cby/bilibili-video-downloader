"""BV input validation and a small command-line interface around yt-dlp."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import parse_qs, urlparse

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


BV_PATTERN = re.compile(r"[Bb][Vv][0-9A-Za-z]{10}")


def positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("请输入正整数") from exc
    if number < 1:
        raise argparse.ArgumentTypeError("请输入正整数")
    return number


def parse_video(value: str) -> tuple[str, int | None]:
    """Accept only a BV ID or a bilibili.com video URL, retaining its page."""
    value = value.strip()
    page = None
    if BV_PATTERN.fullmatch(value):
        bvid = value
    else:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
            "bilibili.com", "www.bilibili.com", "m.bilibili.com",
        }:
            raise ValueError("请输入完整 BV 号或 bilibili.com/video/BV... 视频链接")
        match = re.fullmatch(r"/video/([Bb][Vv][0-9A-Za-z]{10})/?", parsed.path)
        if not match:
            raise ValueError("视频链接中没有有效的 BV 号")
        bvid = match.group(1)
        query = parse_qs(parsed.query, keep_blank_values=True)
        if "p" in query:
            try:
                if len(query["p"]) != 1:
                    raise ValueError
                page = int(query["p"][0])
                if page < 1:
                    raise ValueError
            except ValueError as exc:
                raise ValueError("视频链接的 p 参数必须是正整数") from exc
    return "BV" + bvid[2:], page


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="输入 BV 号下载 B 站视频；省略 BV 号时进入交互输入。",
    )
    parser.add_argument("video", nargs="?", help="BV 号或 B 站视频链接")
    parser.add_argument("-o", "--output", type=Path, default=Path("downloads"),
                        help="保存目录，默认：当前目录下的 downloads")
    pages = parser.add_mutually_exclusive_group()
    pages.add_argument("-p", "--page", type=positive_int, help="下载指定分 P（默认第 1 P）")
    pages.add_argument("--all-parts", action="store_true", help="下载该 BV 的全部分 P")
    parser.add_argument("--max-height", type=positive_int, help="限制最高分辨率，如 720、1080")
    parser.add_argument("--cookies", type=Path, help="Netscape 格式 Cookie 文件路径")
    parser.add_argument("--info", action="store_true", help="只查询视频信息，不下载")
    return parser


def find_ffmpeg() -> str | None:
    # Also support running .conda/python.exe directly without conda activation.
    for directory in (Path(sys.prefix) / "Library" / "bin", Path(sys.prefix) / "bin"):
        if any((directory / name).is_file() for name in ("ffmpeg.exe", "ffmpeg")):
            return str(directory)
    return shutil.which("ffmpeg")


def build_options(args: argparse.Namespace, bvid: str, ffmpeg: str | None) -> dict:
    limit = f"[height<=?{args.max_height}]" if args.max_height else ""
    options = {
        "format": f"bv{limit}+ba/b{limit}",
        "outtmpl": str(args.output.expanduser().resolve() / bvid / "%(title).120B [%(id)s].%(ext)s"),
        "windowsfilenames": True,
        "merge_output_format": "mp4",
        "postprocessors": [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}],
        "noplaylist": not args.all_parts,
        "extractor_args": {"bilibili": {"skip": ["ai"]}},
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
        "continuedl": True,
        "overwrites": False,
        "skip_unavailable_fragments": False,
        "cachedir": False,
        "quiet": args.info,
    }
    if ffmpeg:
        options["ffmpeg_location"] = ffmpeg
    if args.cookies:
        options["cookiefile"] = str(args.cookies.expanduser().resolve())
    return options


def show_info(info: dict) -> None:
    if info.get("_type") in {"playlist", "multi_video"}:
        for entry in info.get("entries") or []:
            if entry:
                show_info(entry)
        return
    print(f"标题：{info.get('title', '未知')}")
    print(f"UP 主：{info.get('uploader') or '未知'}")
    print(f"时长：{info.get('duration') or '未知'} 秒")
    heights = sorted({f["height"] for f in info.get("formats", []) if f.get("height")})
    print("可用分辨率：" + (", ".join(f"{h}p" for h in heights) or "未知"))


def main(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        video = args.video if args.video is not None else input("请输入 BV 号或视频链接：")
        bvid, url_page = parse_video(video)
        if args.cookies and not args.cookies.expanduser().is_file():
            raise ValueError(f"Cookie 文件不存在：{args.cookies}")
        ffmpeg = find_ffmpeg()
        if not args.info and not ffmpeg:
            raise ValueError("未找到 FFmpeg，请激活项目 Conda 环境或运行 conda install -c conda-forge ffmpeg")
        url = f"https://www.bilibili.com/video/{bvid}/"
        if not args.all_parts:
            url += f"?p={args.page or url_page or 1}"
        options = build_options(args, bvid, ffmpeg)
        if not args.info:
            args.output.expanduser().resolve().mkdir(parents=True, exist_ok=True)
        with YoutubeDL(options) as downloader:
            info = downloader.extract_info(url, download=not args.info)
            if not info:
                raise ValueError("未获取到视频信息，请检查 BV 号及视频访问权限")
            if args.info:
                show_info(info)
            else:
                print(f"\n下载完成，保存目录：{args.output.expanduser().resolve() / bvid}")
        return 0
    except (ValueError, OSError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except DownloadError as exc:
        print(f"下载失败：{exc}", file=sys.stderr)
        print("请检查网络、BV 号和视频权限；登录或风控提示可尝试 --cookies cookies.txt。"
              "接口发生变化时可运行 python -m pip install -U yt-dlp。", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\n已取消；再次执行相同命令可续传未完成的下载。", file=sys.stderr)
        return 130
