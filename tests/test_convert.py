import unittest

from html2md.core import convert


class TestHeadingsAndParagraphs(unittest.TestCase):
    def test_headings(self):
        md = convert("<h1>大标题</h1><h2>小节</h2><h6>深层</h6>")
        self.assertEqual(md, "# 大标题\n\n## 小节\n\n###### 深层\n")

    def test_paragraphs_split(self):
        md = convert("<p>第一段</p><p>第二段</p>")
        self.assertEqual(md, "第一段\n\n第二段\n")

    def test_entities_decoded(self):
        md = convert("<p>A &amp; B &#20013; &lt;tag&gt;</p>")
        self.assertEqual(md, "A & B 中 <tag>\n")

    def test_br(self):
        md = convert("<p>一行<br>两行</p>")
        self.assertEqual(md, "一行\n两行\n")

    def test_hr(self):
        self.assertEqual(convert("<p>前</p><hr><p>后</p>"), "前\n\n---\n\n后\n")


class TestInline(unittest.TestCase):
    def test_basic_marks(self):
        md = convert("<p><strong>粗</strong>与<em>斜</em>和<code>码</code>与<del>删</del></p>")
        self.assertEqual(md, "**粗**与*斜*和`码`与~~删~~\n")

    def test_nested_inline(self):
        md = convert("<p><b>粗<b>内</b>外</b></p>")
        self.assertEqual(md, "**粗**内**外**\n")

    def test_inline_between_chars(self):
        md = convert("<p>前<b>中</b>后</p>")
        self.assertEqual(md, "前**中**后\n")

    def test_whitespace_collapsed(self):
        md = convert("<p>多   空格\n\t与换行   都折叠</p>")
        self.assertEqual(md, "多 空格 与换行 都折叠\n")


class TestLinksImages(unittest.TestCase):
    def test_link(self):
        self.assertEqual(convert('<a href="https://a.com">站点</a>'), "[站点](https://a.com)\n")

    def test_link_without_href_keeps_text(self):
        self.assertEqual(convert("<a>纯文字</a>"), "纯文字\n")

    def test_relative_link_with_base(self):
        md = convert('<a href="/post/1">文</a>', base_url="https://a.com/blog/")
        self.assertEqual(md, "[文](https://a.com/post/1)\n")

    def test_link_brackets_escaped(self):
        md = convert('<a href="x">[标]</a>')
        self.assertEqual(md, "[\\[标\\]](x)\n")

    def test_image(self):
        md = convert('<img src="pic.png" alt="说明">')
        self.assertEqual(md, "![说明](pic.png)\n")

    def test_image_relative_base(self):
        md = convert('<img src="p/1.png">', base_url="https://a.com/b/")
        self.assertEqual(md, "![](https://a.com/b/p/1.png)\n")


class TestLists(unittest.TestCase):
    def test_unordered(self):
        md = convert("<ul><li>甲</li><li>乙</li></ul>")
        self.assertEqual(md, "- 甲\n- 乙\n")

    def test_ordered(self):
        md = convert("<ol><li>一</li><li>二</li><li>三</li></ol>")
        self.assertEqual(md, "1. 一\n2. 二\n3. 三\n")

    def test_nested(self):
        md = convert("<ul><li>外<ul><li>内一</li><li>内二</li></ul></li><li>外二</li></ul>")
        self.assertEqual(md, "- 外\n  - 内一\n  - 内二\n- 外二\n")


class TestBlockquotePre(unittest.TestCase):
    def test_quote(self):
        md = convert("<blockquote><p>一句</p><p>两句</p></blockquote>")
        self.assertEqual(md, "> 一句\n>\n> 两句\n")

    def test_pre_code_fence(self):
        md = convert("<pre><code>def f():\n    return 1</code></pre>")
        self.assertEqual(md, "```\ndef f():\n    return 1\n```\n")

    def test_pre_preserves_whitespace(self):
        md = convert("<pre>  缩进\n    更深</pre>")
        self.assertEqual(md, "```\n  缩进\n    更深\n```\n")


class TestStrip(unittest.TestCase):
    def test_script_style_removed(self):
        md = convert("<script>alert(1)</script><style>p{}</style><p>正文</p>")
        self.assertEqual(md, "正文\n")

    def test_nav_aside_removed(self):
        md = convert("<nav>菜单</nav><p>正文</p><aside>侧栏</aside>")
        self.assertEqual(md, "正文\n")

    def test_strip_configurable(self):
        md = convert("<nav>保留我</nav><p>正文</p>", strip=("script",))
        self.assertIn("保留我", md)

    def test_nested_strip(self):
        md = convert("<div><script><style>x</style></script><p>正文</p></div>")
        self.assertEqual(md, "正文\n")


class TestTable(unittest.TestCase):
    def test_gfm_table_with_th(self):
        md = convert("<table><tr><th>名</th><th>值</th></tr>"
                     "<tr><td>a</td><td>1</td></tr></table>")
        self.assertEqual(md, "| 名 | 值 |\n| --- | --- |\n| a | 1 |\n")

    def test_table_without_th(self):
        md = convert("<table><tr><td>x</td><td>y</td></tr></table>")
        self.assertEqual(md, "| x | y |\n| --- | --- |\n")

    def test_cell_pipe_escaped(self):
        md = convert("<table><tr><td>a|b</td></tr></table>")
        self.assertIn("a\\|b", md)


class TestRobustness(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(convert(""), "")
        self.assertEqual(convert("   "), "")

    def test_plain_fragment(self):
        self.assertEqual(convert("裸文本"), "裸文本\n")

    def test_unclosed_tags_tolerated(self):
        md = convert("<ul><li>一<li>二")
        self.assertEqual(md, "- 一\n- 二\n")

    def test_div_blocks_split(self):
        md = convert("<div><p>甲</p></div><div><p>乙</p></div>")
        self.assertEqual(md, "甲\n\n乙\n")


if __name__ == "__main__":
    unittest.main()
