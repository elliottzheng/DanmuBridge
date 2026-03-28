# DanmuBridge

[English](README.md) | [简体中文](README.zh-CN.md)

DanmuBridge downloads Bilibili bangumi danmaku, converts it to `.ass`, and attaches the result to a Jellyfin series folder as external subtitles.

DanmuBridge is a cross-platform Python CLI. The examples below use generic paths and are not Windows-specific.

## Author

- GitHub: [Elliott Zheng](https://github.com/elliottzheng)
- PyPI: `elliottzheng`

## Installation

Install from PyPI:

```bash
pip install danmubridge
```

Install directly from GitHub:

```bash
pip install git+https://github.com/elliottzheng/danmubridge.git
```

For local development from source:

```bash
pip install .
```

After installation, use the `danmubridge` CLI.

## Getting the season_id

This project needs the Bilibili bangumi `season_id`.
In normal Bilibili URLs, this is the number after `ss` in the bangumi play page.

Example:

```text
https://www.bilibili.com/bangumi/play/ss34430
```

In this case, the `season_id` is `34430`.

Another example from the reference project documentation:

```text
https://www.bilibili.com/bangumi/play/ss844/?from=search
```

In this case, the `season_id` is `844`.

Important:

- Do not enter the episode `cid`
- Do not enter the `ep` number from `.../ep123456`
- For this CLI, `34430` means the bangumi `season_id`

## Quick Start

The main entrypoint is `sync`, which downloads danmaku, converts it to ASS, and attaches it to your Jellyfin season folder in one command:

```bash
danmubridge sync 34430 /media/anime/Jujutsu.Kaisen.S01 --replace
```

## Jellyfin Folder Requirement

The target season folder must already contain the video files.
The number of video files in that folder must match the number of generated subtitle files.

For example, if the bangumi has 24 episodes, the target folder should contain 24 video files such as:

```text
Jujutsu.Kaisen.S01E01.mkv
Jujutsu.Kaisen.S01E02.mkv
...
Jujutsu.Kaisen.S01E24.mkv
```

If the subtitle count and video count do not match, the command will stop instead of guessing.

## Other Commands

Use `fetch` when you only want to download and generate ASS subtitles:

```bash
danmubridge fetch 34430
```

By default, the output directory is separated by `season_id`, for example:

```text
generated_danmaku_ass/ss34430/
```

If you want to control the output path yourself:

```bash
danmubridge fetch 34430 --output-dir /data/subtitles/jujutsu-kaisen
```

Use `attach` when you already have generated subtitles and only want to copy them into a Jellyfin folder:

```bash
danmubridge attach /media/anime/Jujutsu.Kaisen.S01 --season-id 34430 --replace
```

If you do not want to use the default inferred subtitle directory, you can pass it explicitly:

```bash
danmubridge attach /media/anime/Jujutsu.Kaisen.S01 --source-dir /data/subtitles/jujutsu-kaisen --replace
```

## CLI Overview

`danmubridge` provides three subcommands:

- `sync`
  End-to-end entrypoint that runs both steps
- `fetch`
  Downloads danmaku and generates ASS files
- `attach`
  Copies generated subtitles into a Jellyfin season folder

## Requirements

- Python 3.10+
- Network access to Bilibili and GitHub

`brotli` is installed automatically as a normal dependency, so the CLI can handle `br`-compressed responses without extra setup.

## Default Paths

- Generated ASS subtitles: `generated_danmaku_ass/ss<season_id>/`
- Temporary cache: user cache directory under `danmubridge/danmaku_cache/ss<season_id>/`
- Downloaded converter: user cache directory under `danmubridge/danmaku2ass/`

These paths can be overridden with CLI arguments.

## Notes

- Subtitles are matched to videos by episode order.
- Video files are sorted by `SxxEyy` when available.
- Existing `*.jpn.ass` files require `--replace` to overwrite.
- `danmaku2ass` is downloaded automatically on first run and stored in the user cache directory, not in your media folder.

## Reference

The `season_id` explanation above is aligned with the usage notes in the BiliDanmaku repository:
https://github.com/fangxx3863/BiliDanmaku

## License

MIT
