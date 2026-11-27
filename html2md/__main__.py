"""命令行入口：

    python -m html2md page.html -o page.md
    python -m html2md page.html --base-url https://example.com/blog/ -o out.md
    cat page.html | python -m html2md -            # stdin 模式
    python -m html2md page.html --strip nav,aside,footer
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .core import DEFAULT_STRIP, convert


def _configure_standard_streams() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def main(argv=None) -> int:
    _configure_standard_streams()
    ap = argparse.ArgumentParser(prog="html2md", description="HTML 转 Markdown（标准库实现）")
    ap.add_argument("--version", action="version", version=f"html2md {__version__}")
    ap.add_argument("input", help="HTML 文件路径；'-' 表示读 stdin")
    ap.add_argument("-o", "--output", help="输出 Markdown 路径（缺省打印到 stdout）")
    ap.add_argument("--base-url", default="", help="相对链接的基准 URL")
    ap.add_argument("--strip", default=",".join(DEFAULT_STRIP),
                    help="剥离的标签（逗号分隔，默认 script,style,nav,aside,noscript,template）")
    args = ap.parse_args(argv)

    if args.input == "-":
        html = sys.stdin.read()
    else:
        src = Path(args.input)
        if not src.exists():
            print(f"错误：文件不存在 {src}", file=sys.stderr)
            return 1
        html = src.read_text(encoding="utf-8-sig")

    strip = tuple(t.strip() for t in args.strip.split(",") if t.strip())
    md = convert(html, base_url=args.base_url, strip=strip)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        lines = md.count("\n") + 1
        print(f"已转换 {lines} 行 → {out}")
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
