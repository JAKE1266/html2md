"""HTML → Markdown 转换核心（基于标准库 html.parser）。

覆盖：标题、段落、行内样式（粗体/斜体/删除线/行内代码）、链接、图片、
有序与无序列表（含嵌套）、引用、围栏代码块、分隔线、GFM 表格；
script/style/nav 等噪声块默认剥离。
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin

DEFAULT_STRIP = ("script", "style", "head", "title", "nav", "aside", "noscript", "template")
_BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li",
               "blockquote", "pre", "hr", "table", "tr", "div", "section",
               "article", "main", "figure", "figcaption", "dl", "dt", "dd"}

_HEADING = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}
_INLINE_WRAP = {"strong": "**", "b": "**", "em": "*", "i": "*", "del": "~~", "s": "~~",
                "code": "`", "kbd": "`", "mark": "`"}


class _Cell:
    """表格单元格收集器。"""

    def __init__(self) -> None:
        self.parts: list[str] = []
        self.header = False

    def text(self) -> str:
        return re.sub(r"\s+", " ", "".join(self.parts)).strip().replace("|", "\\|")


class Converter(HTMLParser):
    """流式转换器：``feed(html)`` 后取 ``result``。"""

    def __init__(self, base_url: str = "", strip: tuple[str, ...] = DEFAULT_STRIP):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.strip_tags = set(strip) or set()
        self.out: list[str] = []          # 已完成块（每个元素是一个块的多行文本）
        self.inline: str = ""             # 当前块的行内文本（Markdown 片段已插入）
        # 状态栈
        self.strip_depth = 0              # 剥离标签嵌套深度
        self.quote_depth = 0
        self.quote_marks: list[int] = []  # blockquote 进入时 out 的长度
        self.list_stack: list[dict] = []  # {"ordered": bool, "counter": int}
        self.list_marks: list[int] = []   # 每层列表进入时 out 的长度
        self.pre_depth = 0
        self.pre_buf: list[str] = []
        self.link_stack: list[int] = []   # a 进入时 inline 的长度
        self.href_stack: list[str] = []
        self.table_rows: list[list[_Cell]] | None = None
        self.cell: _Cell | None = None
        self.heading_tag: str | None = None

    # ---------- 工具 ----------
    def _flush_inline(self) -> str:
        text = self.inline.strip()
        self.inline = ""
        return text

    def _push_block(self, text: str, merge: bool = False) -> None:
        text = text.strip("\n")
        if not text:
            return
        if merge and self.out:
            self.out[-1] += "\n" + text
        else:
            self.out.append(text)

    def _push_list_line(self, text: str) -> None:
        """列表条目行：同一列表（含嵌套层）的所有行合并进同一个块。"""
        text = text.strip("\n")
        if not text:
            return
        mark0 = self.list_marks[0] if self.list_marks else None
        self._push_block(text, merge=mark0 is not None and len(self.out) > mark0)

    def _finish_block(self) -> None:
        self._push_block(self._flush_inline())

    @staticmethod
    def _collapse(text: str) -> str:
        return re.sub(r"\s+", " ", text)

    def _add_text(self, data: str) -> None:
        if self.strip_depth:
            if self.pre_depth:
                self.pre_buf.append(data)
            return
        if self.pre_depth:
            self.pre_buf.append(data)
            return
        if self.cell is not None:
            self.cell.parts.append(self._collapse(data))
            return
        if not data:
            return
        piece = self._collapse(data)
        if not piece:
            return
        # 避免在标记符号后多出空格：「**加粗** 」 行内拼接保持紧凑
        if self.inline.endswith(" ") and piece.startswith(" "):
            piece = piece.lstrip()
        if piece:
            self.inline += piece

    # ---------- 标签 ----------
    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: C901
        attrs_d = dict(attrs)
        if self.strip_depth:
            if tag in self.strip_tags:
                self.strip_depth += 1
            return
        if tag in self.strip_tags:
            self._finish_block()
            self.strip_depth = 1
            return
        if self.pre_depth and tag != "pre":
            return  # pre 内不解析任何行内/块结构

        if tag in _HEADING:
            self._finish_block()
            self.inline = _HEADING[tag] + " "
            self.heading_tag = tag
        elif tag == "p":
            self._finish_block()
        elif tag == "br":
            self.inline += "\n"
        elif tag == "hr":
            self._finish_block()
            self._push_block("---")
        elif tag in _INLINE_WRAP:
            self._finish_block_if_heading()
            self.inline += _INLINE_WRAP[tag]
        elif tag == "a":
            self._finish_block_if_heading()
            href = attrs_d.get("href") or ""
            if href and self.base_url:
                href = urljoin(self.base_url, href)
            self.link_stack.append(len(self.inline))
            self.href_stack.append(href)
        elif tag == "img":
            src = attrs_d.get("src") or ""
            if src and self.base_url:
                src = urljoin(self.base_url, src)
            alt = attrs_d.get("alt") or ""
            self.inline += f"![{alt}]({src})"
        elif tag in ("ul", "ol"):
            self._finish_block()
            self.list_stack.append({"ordered": tag == "ol", "counter": 0})
            self.list_marks.append(len(self.out))
        elif tag == "li":
            prev = self.inline
            self.inline = ""
            if prev.strip():  # 未闭合的上一个 li（HTMLParser 不自动补闭合）
                self._push_list_line(prev)
            if not self.list_stack:
                self.list_stack.append({"ordered": False, "counter": 0})
                self.list_marks.append(len(self.out))
            frame = self.list_stack[-1]
            frame["counter"] += 1
            indent = "  " * (len(self.list_stack) - 1)
            marker = f"{frame['counter']}. " if frame["ordered"] else "- "
            self.inline = indent + marker
        elif tag == "blockquote":
            self._finish_block()
            self.quote_depth += 1
            self.quote_marks.append(len(self.out))
        elif tag == "pre":
            self._finish_block()
            self.pre_depth += 1
            self.pre_buf = []
        elif tag == "table":
            self._finish_block()
            self.table_rows = []
        elif tag == "tr":
            self.table_rows = self.table_rows or []
            self.table_rows.append([])
        elif tag in ("td", "th"):
            self.cell = _Cell()
            self.cell.header = tag == "th"

    def _finish_block_if_heading(self) -> None:
        if self.heading_tag:
            self._close_heading()

    def _close_heading(self) -> None:
        tag = self.heading_tag
        self.heading_tag = None
        text = self._flush_inline()
        self._push_block(text)

    def handle_endtag(self, tag: str) -> None:  # noqa: C901
        if self.strip_depth:
            if tag in self.strip_tags:
                self.strip_depth -= 1
            return
        if self.pre_depth and tag != "pre":
            return  # pre 内不处理行内/块结束

        if tag in _HEADING and self.heading_tag == tag:
            self._close_heading()
        elif tag == "p":
            self._finish_block()
        elif tag in _INLINE_WRAP:
            self.inline += _INLINE_WRAP[tag]
        elif tag == "a":
            if self.link_stack:
                start = self.link_stack.pop()
                href = self.href_stack.pop() or ""
                body = self.inline[start:].strip()
                self.inline = self.inline[:start]
                body = body.replace("[", "\\[").replace("]", "\\]")
                self.inline += f"[{body}]({href})" if href else body
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
                if self.list_marks:
                    self.list_marks.pop()
                if not self.list_stack:
                    self._finish_block()
        elif tag == "li":
            text = self.inline
            self.inline = ""
            self._push_list_line(text)  # 保留前导缩进
        elif tag == "blockquote":
            if self.quote_depth:
                self.quote_depth -= 1
                mark = self.quote_marks.pop() if self.quote_marks else len(self.out)
                quoted = self.out[mark:]
                del self.out[mark:]
                if quoted:
                    merged = "\n\n".join(quoted)
                    self._push_block("\n".join(
                        "> " + ln if ln else ">" for ln in merged.split("\n")))
        elif tag == "pre":
            if self.pre_depth:
                self.pre_depth -= 1
                code = "".join(self.pre_buf).strip("\n")
                self.pre_buf = []
                self._push_block(f"```\n{code}\n```")
        elif tag in ("td", "th"):
            if self.cell is not None and self.table_rows and self.table_rows[-1] is not None:
                self.table_rows[-1].append(self.cell)
                self.cell = None
        elif tag == "table":
            self._render_table()
        elif tag in ("div", "section", "article", "main", "figure", "figcaption",
                     "dl", "dt", "dd", "header", "footer"):
            self._finish_block()

    def _render_table(self) -> None:
        rows, self.table_rows = self.table_rows, None
        if not rows:
            return
        rows = [r for r in rows if r]
        if not rows:
            return
        n_cols = max(len(r) for r in rows)
        rows = [r + [_Cell() for _ in range(n_cols - len(r))] for r in rows]
        grid = [[c.text() for c in r] for r in rows]
        header = rows[0][0].header if rows[0] else False
        lines: list[str] = []
        lines.append("| " + " | ".join(grid[0]) + " |")
        lines.append("|" + "|".join(" --- " for _ in grid[0]) + "|")
        for row in (grid[1:] if header else grid[1:]):
            lines.append("| " + " | ".join(row) + " |")
        self._push_block("\n".join(lines))

    def handle_data(self, data: str) -> None:
        self._add_text(data)

    def result(self) -> str:
        text = self.inline
        self.inline = ""
        if self.list_stack:  # 未闭合的列表：最后一条 li 按列表行合并（保留缩进）
            self._push_list_line(text)
        else:
            self._push_block(text.strip())
        if self.pre_depth and self.pre_buf:  # 未闭合的 pre 也输出
            code = "".join(self.pre_buf).strip("\n")
            self.out.append(f"```\n{code}\n```")
            self.pre_depth = 0
            self.pre_buf = []
        blocks: list[str] = []
        for block in self.out:
            block = re.sub(r"\n{3,}", "\n\n", block).strip()
            if block:
                blocks.append(block)
        return "\n\n".join(blocks) + ("\n" if blocks else "")


def convert(html: str, base_url: str = "",
            strip: tuple[str, ...] = DEFAULT_STRIP) -> str:
    """HTML 文本 → Markdown 文本。"""
    parser = Converter(base_url=base_url, strip=strip)
    parser.feed(html)
    parser.close()
    return parser.result()
