#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${VENV_DIR:-${PROJECT_ROOT}/.venv}"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "ERROR: Required command not found: $1"
        exit 1
    fi
}

is_sourced() {
    [[ "${BASH_SOURCE[0]}" != "${0}" ]]
}

check_python_venv_support() {
    if ! "${PYTHON_BIN}" -m venv --help >/dev/null 2>&1; then
        echo "ERROR: Python venv support is unavailable for ${PYTHON_BIN}"
        echo "Install the OS package that provides 'venv' and rerun this script."
        exit 1
    fi
}

create_venv() {
    if [[ -d "${VENV_DIR}" ]]; then
        echo "Using existing virtual environment at: ${VENV_DIR}"
        return
    fi

    echo "Creating virtual environment at: ${VENV_DIR}"
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
}

activate_venv() {
    # shellcheck disable=SC1091
    source "${VENV_DIR}/bin/activate"
    echo "Activated virtual environment: ${VENV_DIR}"
}

install_python_dependencies() {
    echo "Installing dependencies from: ${REQUIREMENTS_FILE}"
    python -m pip install --disable-pip-version-check -r "${REQUIREMENTS_FILE}"
}

check_linux_portaudio_runtime() {
    if [[ "$(uname -s)" != "Linux" ]]; then
        return 0
    fi

    if python - <<'PY'
import ctypes
import sys

for lib_name in ("libportaudio.so.2", "libportaudio.so"):
    try:
        ctypes.CDLL(lib_name)
        sys.exit(0)
    except OSError:
        continue
sys.exit(1)
PY
    then
        return 0
    fi

    echo "ERROR: PortAudio runtime library is missing."
    echo "Install it, then rerun this script:"
    echo "  sudo apt update && sudo apt install -y libportaudio2"
    exit 1
}

verify_runtime_imports() {
    python - <<'PY'
import sounddevice  # noqa: F401
import speech_recognition  # noqa: F401
print("Verified Python audio dependencies.")
PY
}

require_command "${PYTHON_BIN}"
check_python_venv_support

echo "Using Python: ${PYTHON_BIN}"
create_venv
activate_venv
install_python_dependencies
check_linux_portaudio_runtime
verify_runtime_imports

echo "Setup complete!"
if is_sourced; then
    echo "The current shell is using the virtual environment."
else
    echo "Activate the environment with:"
    echo "  source ${VENV_DIR}/bin/activate"
fi
