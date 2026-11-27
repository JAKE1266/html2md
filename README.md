# html2md

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-46%20passing-success)
![Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

HTML 转 Markdown —— 只用标准库 `html.parser` 实现的流式转换器，为「把网页内容收进 Markdown 笔记库」而生。

- **块级**：一~六级标题、段落、分隔线、引用（多层嵌套 `>`）、`br` 换行
- **行内**：`**粗体**` / `*斜体*` / `` `行内码` `` / `~~删除线~~`，可任意嵌套
- **链接图片**：`[文字](href)` 与 `![alt](src)`；`--base-url` 自动把相对链接转绝对（`urljoin`）；链接文字中的 `[` `]` 自动转义
- **列表**：有序 / 无序，嵌套缩进；未闭合的 `<li>` 也能正确收尾
- **代码**：`<pre>` 保留原始空白输出围栏代码块
- **表格**：输出 GFM 表格，首行 `<th>` 作表头，单元格内 `|` 自动转义
- **噪声剥离**：`script / style / head / title / nav / aside / noscript / template` 默认剔除，`--strip` 可自定义
- **实体解码**：`&amp;` `&#20013;` `&lt;` 等自动还原

零第三方依赖（转换器本身），Python ≥ 3.8。

## 安装

```bash
pip install html2md-kit
python -m html2md --help
```

也可执行 `pip install .` 从源码安装。PyPI 发行名为 `html2md-kit`，Python 模块名与 CLI 命令仍为 `html2md`。

## 真实运行示例

对 `samples/page.html`（一篇带导航、列表、引用、代码块、表格的演示文章）：

```console
$ python -m html2md samples/page.html --base-url https://blog.example.com/posts/ -o page.md
已转换 29 行 → page.md
```

转换结果（节选）：

```markdown
# 探索中文内容工具箱

这是一篇演示文章，讲的是 **开源** 与 *写作* 的关系， 以及 `markdown` 在内容流水线中的位置。

## 为什么做小工具

- 小而美，容易维护
- 零依赖，装完即用
- 测试齐全，改起来放心

## 延伸阅读

1. 先读 [开源项目集总览](https://blog.example.com/posts/open-source.html)
2. 再看 [外部指南](https://example.com/guide)

> 工具是思想的放大器。

```

安装发布版并转换文件：

```bash
pip install html2md-kit
python -m html2md page.html -o page.md
```

| 模块 | 职责 |
| --- | --- |
| `html2md/core.py` | 流式解析 HTML 并渲染 Markdown |
| `html2md/__main__.py` | 命令行入口与 UTF-8 输入输出 |

管道模式与自定义剥离：

```console
$ cat page.html | python -m html2md - --strip script,style
```

## 作为库使用

```python
from html2md import convert

convert("<h1>标题 <strong>重点</strong></h1><p>正文 <b>加粗</b>。</p>")
# '# 标题 **重点**\n\n正文 **加粗**。\n'

convert('<a href="/p/1">文</a>', base_url="https://a.com/blog/")
# '[文](https://a.com/p/1)\n'
```

## 设计取舍

- **单遍流式**：一次 `feed` 完成转换，无 DOM 树、无递归，O(文本长度)
- **行内栈拼接**：粗体/斜体等用前后缀标记直接拼接，嵌套组合天然正确
- **引用区间前缀化**：blockquote 离开时对其间产生的块统一加 `> `，块间空行补 `>`
- **列表单块合并**：同一列表（含嵌套层）的所有条目行合并进同一个 Markdown 块，行距紧凑、缩进保留
- **空白折叠**：正文连续空白折叠为一个空格；`pre` 内原样保留
- **不追求 100% 网页还原**：目标场景是「文章正文」，表格支持单层，嵌套表格等按段落降级

## 运行测试

```bash
python -m unittest discover -s tests
# Ran 46 tests ... OK
```


## 项目结构

```
html2md/
├── .github/
├── CHANGELOG.md
├── LICENSE
├── MANIFEST.in
├── html2md/
├── pyproject.toml
├── samples/
├── tests/
└── README.md
```

## License

MIT
