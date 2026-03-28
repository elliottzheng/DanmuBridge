from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .attach import copy_subtitles_to_jellyfin, resolve_source_dir
from .fetch import (
    DEFAULT_DURATION,
    DEFAULT_FONT,
    DEFAULT_FONT_SIZE,
    generate_danmaku_ass,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="下载 B 站弹幕、转换为 ASS，并复制到 Jellyfin 目录伪装成日语外挂字幕。"
    )
    parser.add_argument("season_id", help="番剧 season_id")
    parser.add_argument("target_dir", help="Jellyfin 番剧目录")
    parser.add_argument("--font", default=DEFAULT_FONT, help=f"字体名称，默认 {DEFAULT_FONT}")
    parser.add_argument(
        "--font-size",
        type=float,
        default=DEFAULT_FONT_SIZE,
        help=f"字体大小，默认 {DEFAULT_FONT_SIZE}",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=DEFAULT_DURATION,
        help=f"滚动/静止弹幕显示秒数，默认 {DEFAULT_DURATION}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="ASS 输出目录，不传则使用默认目录",
    )
    parser.add_argument(
        "--temp-dir",
        type=Path,
        default=None,
        help="临时目录，不传则使用默认目录",
    )
    parser.add_argument(
        "--lang",
        default="jpn",
        help="复制到 Jellyfin 时使用的字幕语言代码，默认 jpn",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="如果目标字幕已存在则覆盖",
    )
    parser.add_argument(
        "--copy-only",
        action="store_true",
        help="跳过下载和转换，只执行复制",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印复制计划，不实际写入 Jellyfin 目录",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    try:
        if args.copy_only:
            source_dir = resolve_source_dir(args.output_dir)
        else:
            source_dir = generate_danmaku_ass(
                season_id=args.season_id,
                font=args.font,
                font_size=args.font_size,
                duration=args.duration,
                output_dir=args.output_dir,
                temp_dir=args.temp_dir,
            )

        copied = copy_subtitles_to_jellyfin(
            source_dir=source_dir,
            target_dir=Path(args.target_dir).resolve(),
            language=args.lang,
            replace=args.replace,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        print(f"执行失败: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"Dry run 完成，共计划处理 {copied} 个字幕文件。")
    else:
        print(f"全部完成，共处理 {copied} 个字幕文件。")
    return 0


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
