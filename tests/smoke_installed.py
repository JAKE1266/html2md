import os
import shutil
import subprocess
import sys
import tempfile
from importlib import metadata
from pathlib import Path

import html2md

ROOT = Path(__file__).resolve().parent.parent
DIST_NAME = "html2md-kit"
VERSION = "0.1.1"


def run(*args, stdin_bytes=b"", expect=0):
    env = os.environ.copy()
    env.update(PYTHONIOENCODING="cp1252", PYTHONUTF8="0")
    result = subprocess.run(args, input=stdin_bytes, capture_output=True, env=env)
    assert result.returncode == expect, (args, result.returncode, result.stderr)
    return result


def main():
    dist = metadata.distribution(DIST_NAME)
    assert dist.metadata["Name"] == DIST_NAME
    assert dist.version == VERSION
    assert dist.metadata["Requires-Python"] == ">=3.8"
    module_path = Path(html2md.__file__).resolve()
    assert ROOT != module_path and ROOT not in module_path.parents, module_path
    assert html2md.__version__ == VERSION

    source = ('<h1>中文 <strong>标题</strong></h1>'
              '<h2><a href="/g">阅读 <em>指南</em></a></h2>')
    expected = ('# 中文 **标题**\n\n'
                '## [阅读 *指南*](https://a.com/g)\n')
    result = run(sys.executable, "-m", "html2md", "-", "--base-url",
                 "https://a.com/", stdin_bytes=source.encode("utf-8"))
    stdout = result.stdout.decode("utf-8").replace("\r\n", "\n")
    assert stdout == expected, stdout

    executable = shutil.which("html2md")
    assert executable, "html2md console script not found"
    result = run(executable, "--version")
    assert result.stdout.decode("utf-8").strip() == f"html2md {VERSION}"

    with tempfile.TemporaryDirectory() as tmp:
        missing = str(Path(tmp) / "missing.html")
        result = run(sys.executable, "-m", "html2md", missing, expect=1)
        assert "文件不存在".encode("utf-8") in result.stderr

    print(f"installed smoke passed: {DIST_NAME} {VERSION}")


if __name__ == "__main__":
    main()
