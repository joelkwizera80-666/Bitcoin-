#!/usr/bin/env bash
# Idempotent Cloud Agent install for the Bitcoin- Python project.
# Safe to run repeatedly and on a fresh default image or a snapshot base.
set -euo pipefail

cd "$(dirname "$0")/.."

# Ensure the venv module can bootstrap pip. The default image ships Python 3.12
# but not always the matching python3-venv (ensurepip) package.
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  PYVER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  sudo apt-get update -y
  sudo apt-get install -y "python3.${PYVER#*.}-venv" || sudo apt-get install -y python3-venv
fi

python3 -m venv .venv
# shellcheck source=/dev/null
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "install.sh: done"
