#!/usr/bin/env bash
# Geliştirme/SessionStart kurulumu — idempotent. Backend venv + bağımlılıklar,
# mobil node_modules. Var olanları atlar.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "[usta] backend kurulumu..."
if [ ! -d backend/.venv ]; then
  python3 -m venv backend/.venv
fi
backend/.venv/bin/pip install -q --upgrade pip >/dev/null
backend/.venv/bin/pip install -q -r backend/requirements.txt

echo "[usta] mobil kurulumu..."
if [ ! -d mobile/node_modules ]; then
  (cd mobile && npm install --no-audit --no-fund >/dev/null 2>&1 || true)
else
  echo "[usta] mobil node_modules mevcut, atlanıyor"
fi

echo "[usta] kurulum tamam. Testler: (cd backend && .venv/bin/python -m pytest -q)"
