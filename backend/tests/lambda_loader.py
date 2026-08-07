"""ドメイン別 Lambda ディレクトリをトップレベルモジュールとして読み込む。

health / attendance / leave がいずれも `handler.py` を持つため、PYTHONPATH を
並べるだけではモジュールキャッシュが衝突する。テストは本ヘルパ経由で
対象ディレクトリだけを先頭に載せ替えて import する。
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

BACKEND = Path(__file__).resolve().parents[1]
_LAMBDA_DIRS = ("health", "attendance", "leave")
_LAMBDA_MODULES = ("handler", "auth", "service", "repository", "errors")


def import_lambda(name: str) -> ModuleType:
    root = BACKEND / name
    if not root.is_dir():
        raise FileNotFoundError(root)

    for key in list(sys.modules):
        if key in _LAMBDA_MODULES or key.startswith(tuple(f"{m}." for m in _LAMBDA_MODULES)):
            del sys.modules[key]

    # 他ドメインのパスを除き、対象を先頭へ
    excluded = {(BACKEND / d).resolve() for d in _LAMBDA_DIRS}
    filtered = [p for p in sys.path if Path(p).resolve() not in excluded]
    sys.path[:] = [str(root), *filtered]
    return importlib.import_module("handler")
