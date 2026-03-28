from __future__ import annotations

import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_OUTPUT_DIR_NAME = "generated_danmaku_ass"
LEGACY_OUTPUT_DIR_NAME = "AssOut"
DEFAULT_TEMP_DIR_NAME = "danmaku_cache"
LEGACY_TEMP_DIR_NAME = "BiliTmp"
DEFAULT_FONT = "黑体"
DEFAULT_FONT_SIZE = 30.0
DEFAULT_DURATION = 8.0
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


def get_project_root() -> Path:
    return Path.cwd()


def get_cache_root() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "danmubridge"


def season_folder_name(season_id: str) -> str:
    season_id = season_id.strip()
    return season_id if season_id.startswith("ss") else f"ss{season_id}"


def get_default_output_root() -> Path:
    return get_project_root() / DEFAULT_OUTPUT_DIR_NAME


def get_default_output_dir(season_id: str) -> Path:
    return get_default_output_root() / season_folder_name(season_id)


def get_legacy_output_dir() -> Path:
    return get_project_root() / LEGACY_OUTPUT_DIR_NAME


def get_default_temp_root() -> Path:
    return get_cache_root() / DEFAULT_TEMP_DIR_NAME


def get_default_temp_dir(season_id: str) -> Path:
    return get_default_temp_root() / season_folder_name(season_id)


def get_legacy_temp_dir() -> Path:
    return get_project_root() / LEGACY_TEMP_DIR_NAME


def get_danmaku2ass_dir() -> Path:
    return get_cache_root() / "danmaku2ass"


def download_bytes(url: str, *, headers: dict[str, str] | None = None) -> bytes:
    request = Request(url, headers=headers or {})
    with urlopen(request) as response:
        payload = response.read()
        content_encoding = response.headers.get("Content-Encoding", "").lower()

    if content_encoding == "gzip":
        try:
            return gzip.decompress(payload)
        except OSError:
            return payload
    if content_encoding == "deflate":
        for wbits in (zlib.MAX_WBITS, -zlib.MAX_WBITS):
            try:
                return zlib.decompress(payload, wbits)
            except zlib.error:
                continue
        return payload
    if content_encoding == "br":
        import brotli

        try:
            return brotli.decompress(payload)
        except brotli.error:
            return payload
    return payload


def ensure_danmaku2ass() -> Path:
    danmaku2ass_dir = get_danmaku2ass_dir()
    script_path = danmaku2ass_dir / "danmaku2ass.py"
    if script_path.exists():
        return script_path

    archive_url = "https://codeload.github.com/m13253/danmaku2ass/zip/refs/heads/master"
    print("下载 danmaku2ass...")
    archive_data = download_bytes(archive_url, headers={"User-Agent": USER_AGENT})

    cache_root = get_cache_root()
    cache_root.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
        temp_file.write(archive_data)
        temp_zip_path = Path(temp_file.name)

    extract_root = cache_root / ".tmp_danmaku2ass"
    if extract_root.exists():
        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True)

    try:
        with zipfile.ZipFile(temp_zip_path) as archive:
            archive.extractall(extract_root)

        extracted_dirs = [path for path in extract_root.iterdir() if path.is_dir()]
        if not extracted_dirs:
            raise RuntimeError("danmaku2ass 下载成功，但解压结果为空。")

        extracted_dir = extracted_dirs[0]
        if danmaku2ass_dir.exists():
            shutil.rmtree(danmaku2ass_dir)
        shutil.move(str(extracted_dir), str(danmaku2ass_dir))
    finally:
        temp_zip_path.unlink(missing_ok=True)
        shutil.rmtree(extract_root, ignore_errors=True)

    if not script_path.exists():
        raise RuntimeError("未找到 danmaku2ass.py，依赖初始化失败。")
    return script_path


def prompt(text: str) -> str:
    return input(text).strip()


def resolve_output_dir(season_id: str, output_dir: Path | None = None) -> Path:
    if output_dir is not None:
        return output_dir.resolve()
    default_output_dir = get_default_output_dir(season_id)
    legacy_output_dir = get_legacy_output_dir()
    if default_output_dir.exists() or not legacy_output_dir.exists():
        return default_output_dir
    return legacy_output_dir


def resolve_temp_dir(season_id: str, temp_dir: Path | None = None) -> Path:
    if temp_dir is not None:
        return temp_dir.resolve()
    default_temp_dir = get_default_temp_dir(season_id)
    legacy_temp_dir = get_legacy_temp_dir()
    if default_temp_dir.exists() or not legacy_temp_dir.exists():
        return default_temp_dir
    return legacy_temp_dir


def fetch_episode_cids(season_id: str) -> list[int]:
    query = urlencode({"season_id": season_id})
    url = f"http://bangumi.bilibili.com/web_api/get_ep_list?{query}"
    raw = download_bytes(url, headers={"User-Agent": USER_AGENT})
    payload = json.loads(raw.decode("utf-8"))

    result = payload.get("result")
    if not isinstance(result, list):
        raise RuntimeError(f"接口返回异常: {payload}")

    cids: list[int] = []
    for episode in result:
        cid = episode.get("cid")
        if isinstance(cid, int):
            cids.append(cid)

    if not cids:
        raise RuntimeError("未获取到任何 CID，请确认输入的 season_id 是否正确。")
    return cids


def prepare_directories(output_dir: Path, temp_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    output_dir.mkdir(parents=True)
    temp_dir.mkdir(parents=True)


def download_xml(cid: int, output_path: Path) -> None:
    xml_url = f"https://comment.bilibili.com/{cid}.xml"
    xml_data = download_bytes(xml_url, headers={"User-Agent": USER_AGENT})
    output_path.write_bytes(xml_data)


def convert_xml_to_ass(
    danmaku2ass_script: Path,
    xml_path: Path,
    ass_path: Path,
    font: str,
    font_size: float,
    duration: float,
) -> None:
    subprocess.run(
        [
            sys.executable,
            str(danmaku2ass_script),
            "-o",
            str(ass_path),
            "-s",
            "1920x1080",
            "-fn",
            font,
            "-fs",
            str(font_size),
            "-dm",
            str(duration),
            "-ds",
            str(duration),
            str(xml_path),
        ],
        check=True,
    )


def generate_danmaku_ass(
    season_id: str,
    *,
    font: str = DEFAULT_FONT,
    font_size: float = DEFAULT_FONT_SIZE,
    duration: float = DEFAULT_DURATION,
    output_dir: Path | None = None,
    temp_dir: Path | None = None,
) -> Path:
    output_path = resolve_output_dir(season_id, output_dir)
    temp_path = resolve_temp_dir(season_id, temp_dir)

    print("下载依赖并初始化...")
    danmaku2ass_script = ensure_danmaku2ass()
    print(f"你选择的字体为 {font}")

    prepare_directories(output_path, temp_path)

    cids = fetch_episode_cids(season_id)
    (temp_path / "cid.txt").write_text(
        "\n".join(str(cid) for cid in cids),
        encoding="utf-8",
    )

    try:
        for index, cid in enumerate(cids, start=1):
            print(f"CID: {cid}")
            xml_path = temp_path / f"{index}.xml"
            ass_path = output_path / f"{index}.ass"
            download_xml(cid, xml_path)
            convert_xml_to_ass(
                danmaku2ass_script=danmaku2ass_script,
                xml_path=xml_path,
                ass_path=ass_path,
                font=font,
                font_size=font_size,
                duration=duration,
            )
    finally:
        shutil.rmtree(temp_path, ignore_errors=True)

    print("Comple!")
    print(f"输出目录为 {output_path}")
    print(f"缓存目录为 {get_cache_root()}")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="下载 B 站弹幕并转换为 ASS 字幕。")
    parser.add_argument("season_id", nargs="?", help="番剧 season_id")
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
        help=(
            "输出目录，可自定义；默认会按 season_id 输出到 "
            f"{DEFAULT_OUTPUT_DIR_NAME}/ss<season_id>/"
        ),
    )
    parser.add_argument(
        "--temp-dir",
        type=Path,
        default=None,
        help=(
            "临时目录，可自定义；默认位于用户缓存目录下，并按 season_id 分目录"
        ),
    )
    return parser


def run(args: argparse.Namespace) -> int:
    try:
        season_id = args.season_id.strip() if args.season_id else prompt("输入番剧CID: ")
        if not season_id:
            print("season_id 不能为空。", file=sys.stderr)
            return 1

        generate_danmaku_ass(
            season_id=season_id,
            font=args.font,
            font_size=args.font_size,
            duration=args.duration,
            output_dir=args.output_dir,
            temp_dir=args.temp_dir,
        )
        return 0
    except (HTTPError, URLError) as exc:
        print(f"网络请求失败: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"弹幕转换失败: {exc}", file=sys.stderr)
        return exc.returncode or 1
    except Exception as exc:
        print(f"执行失败: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    return run(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
