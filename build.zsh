#!/bin/zsh
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

# 권한 리셋 옵트인 플래그 (--reset-permissions). 기본값은 리셋 안 함.
# ad-hoc 서명은 재빌드마다 신원이 달라져 과거 빌드의 TCC 권한 항목이 잔존하므로,
# 새 빌드를 깨끗하게 권한 받으려면 이 플래그로 기존 항목을 제거합니다.
RESET_TCC=0
for arg in "$@"; do
  [[ "$arg" == "--reset-permissions" ]] && RESET_TCC=1
done

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

if [[ "$RESET_TCC" == "1" && -x "./reset_permissions.zsh" ]]; then
  echo ""
  echo "Resetting permissions (--reset-permissions)..."
  ./reset_permissions.zsh || true
fi

echo ""
echo "Build completed."
echo "권한 테스트는 내부 바이너리 직접 실행보다 아래 방식이 적절합니다."
echo "open -n \"dist/EbookToPDF.app\""
echo ""
echo "재빌드 후 권한이 풀린다면, 기존 권한 항목을 제거하고 다시 빌드하세요:"
echo "  ./build.zsh --reset-permissions   (또는 ./reset_permissions.zsh)"
