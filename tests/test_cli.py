import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

SAMPLE = ROOT / "samples" / "page.html"


def run_cli(*args, stdin_text=None, expect=0):
    r = subprocess.run([PY, "-m", "html2md", *args], input=stdin_text,
                       capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    if r.returncode != expect:
        raise AssertionError(f"exit={r.returncode} (expect {expect})\n"
                             f"stdout={r.stdout}\nstderr={r.stderr}")
    return r


class TestCli(unittest.TestCase):
    def test_file_to_stdout(self):
        r = run_cli(str(SAMPLE))
        self.assertIn("# 探索中文内容工具箱", r.stdout)
        self.assertIn("**开源**", r.stdout)
        self.assertNotIn("<", r.stdout.split("```")[0].splitlines()[0])

    def test_file_to_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            dst = Path(tmp) / "out.md"
            r = run_cli(str(SAMPLE), "-o", str(dst))
            self.assertIn("已转换", r.stdout)
            self.assertTrue(dst.exists())
            self.assertIn("# 探索中文内容工具箱", dst.read_text(encoding="utf-8"))

    def test_base_url_resolves_links(self):
        r = run_cli(str(SAMPLE), "--base-url", "https://blog.example.com/posts/")
        self.assertIn("(https://blog.example.com/posts/open-source.html)", r.stdout)

    def test_stdin_mode(self):
        r = run_cli("-", stdin_text="<h2>管道输入</h2><p>支持 <code>stdin</code></p>")
        self.assertIn("## 管道输入", r.stdout)
        self.assertIn("`stdin`", r.stdout)

    def test_strip_custom(self):
        r = run_cli(str(SAMPLE), "--strip", "script,nav")
        self.assertIn("aside 内容也会保留", r.stdout)  # aside 未被剥离

    def test_missing_file(self):
        r = run_cli("nope.html", expect=1)
        self.assertIn("文件不存在", r.stderr)


if __name__ == "__main__":
    unittest.main()
