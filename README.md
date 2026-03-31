# DanmuBridge

[简体中文](README.md) | [English](README.en.md)

DanmuBridge 用于下载哔哩哔哩番剧弹幕，将其转换为 `.ass` 字幕，并复制到 Jellyfin 剧集目录中作为外挂字幕使用。

DanmuBridge 是一个跨平台的 Python CLI，下面的示例路径使用中性写法，不限定 Windows。

## 作者

- GitHub: [Elliott Zheng](https://github.com/elliottzheng)
- PyPI: `elliottzheng`

## 安装

从 PyPI 安装：

```bash
pip install danmubridge
```

直接从 GitHub 安装：

```bash
pip install git+https://github.com/elliottzheng/danmubridge.git
```

本地源码开发安装：

```bash
pip install .
```

安装完成后可直接使用 `danmubridge` 命令。

## 如何获取 season_id

这个项目需要的参数是哔哩哔哩番剧的 `season_id`。
通常它就是番剧播放页链接里 `ss` 后面的数字。

例如：

```text
https://www.bilibili.com/bangumi/play/ss34430
```

这里的 `season_id` 就是 `34430`。

再举一个参考项目里的例子：

```text
https://www.bilibili.com/bangumi/play/ss844/?from=search
```

这里的 `season_id` 就是 `844`。

需要注意：

- 不要填单集视频的 `cid`
- 不要填链接里 `.../ep123456` 这种 `ep` 编号
- 在本项目中，`34430` 这种参数表示的是番剧 `season_id`

## 快速开始

主入口命令是 `sync`，它会一条命令完成弹幕下载、ASS 转换和 Jellyfin 外挂字幕复制：

```bash
danmubridge sync 34430 /media/anime/Jujutsu.Kaisen.S01 --replace
```

## Jellyfin 剧集目录要求

目标剧集目录中必须已经存在视频文件。
而且该目录中的视频文件数量，必须和生成出来的字幕文件数量一致。

例如，如果番剧一共有 24 集，那么目标目录中应该有 24 个视频文件，例如：

```text
Jujutsu.Kaisen.S01E01.mkv
Jujutsu.Kaisen.S01E02.mkv
...
Jujutsu.Kaisen.S01E24.mkv
```

如果字幕数量和视频数量不一致，程序会直接停止，而不是猜测如何匹配。

## 其他命令

如果你只想下载并生成 ASS 字幕，可以使用 `fetch`：

```bash
danmubridge fetch 34430
```

默认情况下，输出目录会按番剧 `season_id` 分开，例如：

```text
generated_danmaku_ass/ss34430/
```

如果你希望自定义下载输出目录，可以显式指定：

```bash
danmubridge fetch 34430 --output-dir /data/subtitles/jujutsu-kaisen
```

如果你已经有字幕，只想复制到 Jellyfin 目录，可以使用 `attach`：

```bash
danmubridge attach /media/anime/Jujutsu.Kaisen.S01 --season-id 34430 --replace
```

如果你不想按默认目录推断，也可以手动指定字幕来源目录：

```bash
danmubridge attach /media/anime/Jujutsu.Kaisen.S01 --source-dir /data/subtitles/jujutsu-kaisen --replace
```

## CLI 总览

`danmubridge` 提供 3 个子命令：

- `sync`
  一条命令跑完整流程
- `fetch`
  下载番剧弹幕并生成 ASS 字幕
- `attach`
  将已有字幕复制到 Jellyfin 剧集目录

## 运行要求

- Python 3.10+
- 可以访问 Bilibili 和 GitHub 的网络环境

`brotli` 已经作为正式依赖自动安装，用来处理部分 `br` 压缩响应，用户不需要额外关心。

## 默认输出位置

- 生成的 ASS 字幕：`generated_danmaku_ass/ss<season_id>/`
- 临时缓存：用户缓存目录下的 `danmubridge/danmaku_cache/ss<season_id>/`
- 自动下载的 `danmaku2ass`：用户缓存目录下的 `danmubridge/danmaku2ass/`

这些路径都可以通过 CLI 参数覆盖。

## 说明

- 字幕与视频的匹配方式基于集数顺序。
- 如果视频文件名中包含 `SxxEyy`，会优先按该信息排序。
- 如果目标目录中已存在同名 `*.jpn.ass` 文件，需要使用 `--replace` 覆盖。
- `danmaku2ass` 会在首次运行时自动下载，并缓存到用户目录，不会污染媒体目录。

## 参考

上面关于 `season_id` 的说明，参考了这个项目的使用文档：
https://github.com/fangxx3863/BiliDanmaku

## 许可证

MIT
