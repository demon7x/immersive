#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -U pip >/dev/null
pip install -r requirements.txt

# Some environments export an empty Qt plugin path, which breaks cocoa loading on macOS.
unset QT_QPA_PLATFORM_PLUGIN_PATH || true
unset QT_PLUGIN_PATH || true

QT_PLUGIN_DIR="$(python - <<'PY'
from pathlib import Path
import sys

try:
    from PyQt6.QtCore import QLibraryInfo
    p = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
    if p:
        print(p)
        raise SystemExit(0)
except Exception:
    pass

# Fallback for pip wheels where plugins live under site-packages/PyQt6/Qt6/plugins
for site in sys.path:
    cand = Path(site) / "PyQt6" / "Qt6" / "plugins"
    if cand.exists():
        print(cand)
        raise SystemExit(0)
PY
)"

if [[ -n "${QT_PLUGIN_DIR:-}" ]]; then
  export QT_QPA_PLATFORM_PLUGIN_PATH="${QT_PLUGIN_DIR}/platforms"
  export QT_PLUGIN_PATH="${QT_PLUGIN_DIR}"
fi

python -m app.main "$@"
