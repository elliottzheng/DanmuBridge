from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from .fetch import get_default_output_dir, get_legacy_output_dir


VIDEO_EXTENSIONS = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".ts"}
SUBTITLE_EXTENSIONS = {".ass", ".ssa", ".srt", ".sub"}
EPISODE_PATTERN = re.compile(r"[Ss](\d+)[Ee](\d+)")
NUMBER_PATTERN = re.compile(r"(\d+)")


def natural_key(path: Path) -> tuple[object, ...]:
    parts = NUMBER_PATTERN.split(path.name.lower())
    key: list[object] = []
    for part in parts:
        if not part:
            continue
        key.append(int(part) if part.isdigit() else part)
    return tuple(key)


def episode_key(path: Path) -> tuple[int, int, tuple[object, ...]]:
    match = EPISODE_PATTERN.search(path.stem)
    if match:
        return (int(match.group(1)), int(match.group(2)), natural_key(path))
    return (sys.maxsize, sys.maxsize, natural_key(path))


def resolve_source_dir(season_id: str | None = None, source_dir: Path | None = None) -> Path:
    if source_dir is not None:
        return source_dir.resolve()
    if season_id:
        default_output_dir = get_default_output_dir(season_id)
        if default_output_dir.exists():
            return default_output_dir
    legacy_output_dir = get_legacy_output_dir()
    if legacy_output_dir.exists():
        return legacy_output_dir
    if season_id:
        return get_default_output_dir(season_id)
    raise RuntimeError("未指定 --source-dir，且未提供 season_id 来推断默认字幕目录。")


def list_source_subtitles(source_dir: Path) -> list[Path]:
    subtitles = [
        path
        for path in source_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUBTITLE_EXTENSIONS
    ]
    return sorted(subtitles, key=natural_key)


def list_videos(target_dir: Path) -> list[Path]:
    videos = [
        path
        for path in target_dir.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
    ]
    return sorted(videos, key=episode_key)


def build_destination(video_path: Path, language: str, subtitle_ext: str) -> Path:
    return video_path.with_name(f"{video_path.stem}.{language}{subtitle_ext}")


def copy_subtitles_to_jellyfin(
    source_dir: Path,
    target_dir: Path,
    *,
    language: str = "jpn",
    replace: bool = False,
    dry_run: bool = False,
) -> int:
    subtitles = list_source_subtitles(source_dir)
    videos = list_videos(target_dir)

    if not subtitles:
        raise RuntimeError(f"未在 {source_dir} 中找到字幕文件。")
    if not videos:
        raise RuntimeError(f"未在 {target_dir} 中找到视频文件。")
    if len(subtitles) != len(videos):
        raise RuntimeError(
            f"字幕数量({len(subtitles)})与视频数量({len(videos)})不一致，已停止。"
        )

    print(f"找到 {len(subtitles)} 个字幕文件，{len(videos)} 个视频文件。")

    copied = 0
    for subtitle_path, video_path in zip(subtitles, videos):
        destination = build_destination(video_path, language, subtitle_path.suffix.lower())
        action = "覆盖" if destination.exists() else "复制"
        print(f"{action}: {subtitle_path.name} -> {destination.name}")

        if destination.exists() and not replace:
            raise RuntimeError(
                f"目标文件已存在: {destination}。如需覆盖请加 --replace。"
            )

        if not dry_run:
            shutil.copy2(subtitle_path, destination)
        copied += 1

    return copied


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="将生成的 ASS 字幕按集数复制到 Jellyfin 番剧目录，并伪装成日语外挂字幕。"
    )
    parser.add_argument(
        "target_dir",
        help="Jellyfin 剧集目录",
    )
    parser.add_argument(
        "--season-id",
        default=None,
        help="可选。用于推断默认字幕来源目录，例如 generated_danmaku_ass/ss34430/",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=None,
        help="字幕来源目录。若不传，可结合 --season-id 自动推断",
    )
    parser.add_argument(
        "--lang",
        default="jpn",
        help="外挂字幕语言代码，默认 jpn",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="如果目标字幕已存在则覆盖",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印计划，不实际复制",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    target_dir = Path(args.target_dir).resolve()

    try:
        source_dir = resolve_source_dir(args.season_id, args.source_dir)
        copied = copy_subtitles_to_jellyfin(
            source_dir=source_dir,
            target_dir=target_dir,
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
        print(f"完成，共复制 {copied} 个字幕文件。")
    return 0


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
