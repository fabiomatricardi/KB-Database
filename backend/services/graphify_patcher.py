"""Monkey-patch tiktoken to allow special tokens, then run graphify CLI.

graphify's _estimate_file_tokens() calls encode() without allowed_special,
which crashes when article content contains LLM chat template tokens.
This wrapper patches tiktoken before invoking graphify's CLI entry point.
"""
import subprocess
import sys

# Auto-upgrade graphify if the installed version is too old (< 0.8.39).
# The html and cluster-only commands require a recent version.
subprocess.run(
    [sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "graphifyy>=0.8.46"],
    check=False,
    timeout=60,
)

import tiktoken as _tk

_original_get_encoding = _tk.get_encoding

def _patched_get_encoding(name="cl100k_base"):
    enc = _original_get_encoding(name)
    _orig_encode = enc.encode
    def _safe_encode(text, *args, **kwargs):
        kwargs.setdefault("allowed_special", "all")
        return _orig_encode(text, *args, **kwargs)
    enc.encode = _safe_encode
    return enc

_tk.get_encoding = _patched_get_encoding

from graphify.__main__ import main

sys.argv = ["graphify"] + sys.argv[1:]
main()
