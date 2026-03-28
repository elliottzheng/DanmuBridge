from __future__ import annotations

import argparse

from . import attach, fetch, sync


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="danmubridge",
        description="Bilibili danmaku to Jellyfin subtitle bridge.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="下载 B 站弹幕并转换为 ASS")
    for action in fetch.build_parser()._actions:
        if action.dest != "help":
            fetch_parser._add_action(action)
    fetch_parser.set_defaults(handler=fetch.run)

    attach_parser = subparsers.add_parser("attach", help="复制字幕到 Jellyfin 目录")
    for action in attach.build_parser()._actions:
        if action.dest != "help":
            attach_parser._add_action(action)
    attach_parser.set_defaults(handler=attach.run)

    sync_parser = subparsers.add_parser("sync", help="一键下载、转换并复制字幕")
    for action in sync.build_parser()._actions:
        if action.dest != "help":
            sync_parser._add_action(action)
    sync_parser.set_defaults(handler=sync.run)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
