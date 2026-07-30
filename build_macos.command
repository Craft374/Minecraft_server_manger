#!/bin/zsh

set -e
cd "$(dirname "$0")"

pause_if_interactive() {
    if [[ -t 0 ]]; then
        echo
        echo "아무 키나 누르면 창을 닫습니다."
        read -k 1
    fi
}
trap pause_if_interactive EXIT

if [[ -z "${EMSR_PYTHON:-}" ]]; then
    if [[ -x ".venv/bin/python" ]]; then
        EMSR_PYTHON=".venv/bin/python"
    else
        EMSR_PYTHON="python3"
    fi
fi

if [[ "$EMSR_PYTHON" == */* ]]; then
    PYTHON_FOUND=$([[ -x "$EMSR_PYTHON" ]] && echo "yes" || echo "no")
else
    PYTHON_FOUND=$(command -v "$EMSR_PYTHON" >/dev/null 2>&1 && echo "yes" || echo "no")
fi

if [[ "$PYTHON_FOUND" != "yes" ]]; then
    echo "[EMSR] Python 3을 찾지 못했습니다."
    exit 1
fi

echo "[EMSR] 필요한 패키지를 확인합니다."
"$EMSR_PYTHON" -m pip install -r requirements.txt

echo "[EMSR] macOS 앱을 빌드합니다."
"$EMSR_PYTHON" -m PyInstaller --noconfirm --clean mac_build.spec

echo "[EMSR] 앱에 로컬 서명을 적용합니다."
codesign --force --deep --sign - dist/EMSR.app
codesign --verify --deep --strict dist/EMSR.app

echo
echo "[EMSR] 빌드 완료: dist/EMSR.app"
