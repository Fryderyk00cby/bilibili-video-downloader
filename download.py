"""Convenient source-tree entry point: python download.py BV..."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

if __name__ == "__main__":
    try:
        from bilibili_downloader.cli import main
    except ModuleNotFoundError as exc:
        if exc.name != "yt_dlp":
            raise
        print("缺少依赖，请先创建并激活 Conda 环境，参见 README.md。", file=sys.stderr)
        raise SystemExit(1)
    raise SystemExit(main())
