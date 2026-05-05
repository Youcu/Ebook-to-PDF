#!/bin/zsh
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

rm -rf build dist

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -m py_compile main.py permission_utils.py capture_worker.py

pyinstaller --clean --noconfirm EbookToPDF.spec

codesign --force --deep --sign - dist/EbookToPDF.app
codesign --verify --deep --strict --verbose=2 dist/EbookToPDF.app

if [[ -x "./make_dmg.zsh" ]]; then
  echo ""
  echo "Making DMG..."
  # DMG 생성은 Finder/AppleEvent 등에 민감해서, 앱 빌드가 성공했는데
  # DMG만 실패하면 빌드는 계속 유지하도록 처리합니다.
  ./make_dmg.zsh || {
    echo "Warning: DMG 생성 실패 (앱은 빌드됨): dist/EbookToPDF.dmg"
  }
fi

echo ""
echo "Build completed."
echo "권한 테스트는 내부 바이너리 직접 실행보다 아래 방식이 적절합니다."
echo "open -n \"dist/EbookToPDF.app\""
