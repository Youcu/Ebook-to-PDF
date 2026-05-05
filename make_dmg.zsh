#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

APP_PATH="dist/EbookToPDF.app"
APP_NAME="$(basename "$APP_PATH")"
DMG_NAME="EbookToPDF"
VOL_NAME="EbookToPDF Installer"
OUT_DMG="dist/${DMG_NAME}.dmg"
TMP_DMG="dist/${DMG_NAME}-temp.dmg"
STAGE_DIR="dist/dmg-stage"
MOUNT_DIR="/Volumes/${VOL_NAME}"

if [[ ! -d "$APP_PATH" ]]; then
  echo "앱 번들이 없습니다: $APP_PATH"
  echo "먼저 ./build.zsh 를 실행해 주세요."
  exit 1
fi

rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"

cp -R "$APP_PATH" "$STAGE_DIR/"
ln -s /Applications "$STAGE_DIR/Applications"

rm -f "$OUT_DMG" "$TMP_DMG"

if [[ -d "$MOUNT_DIR" ]] && mount | awk -v mount_path="$MOUNT_DIR" '$0 ~ mount_path { found=1 } END { exit(found ? 0 : 1) }'; then
  hdiutil detach "$MOUNT_DIR" -force || true
fi

SIZE_MB="$(du -sm "$STAGE_DIR" | awk '{print $1}')"
SIZE_MB="$((SIZE_MB + 30))"

hdiutil create \
  -volname "$VOL_NAME" \
  -srcfolder "$STAGE_DIR" \
  -fs HFS+ \
  -fsargs "-c c=64,a=16,e=16" \
  -format UDRW \
  -size "${SIZE_MB}m" \
  "$TMP_DMG"

DEVICE="$(hdiutil attach -readwrite -noverify -noautoopen "$TMP_DMG" | awk '/Apple_HFS/ {print $1}')"

for _ in {1..20}; do
  [[ -d "$MOUNT_DIR" ]] && break
  sleep 0.2
done

osascript <<EOF
tell application "Finder"
  tell disk "${VOL_NAME}"
    open
    set current view of container window to icon view
    set toolbar visible of container window to false
    set statusbar visible of container window to false
    set bounds of container window to {200, 120, 1224, 700}
    set opts to the icon view options of container window
    set arrangement of opts to not arranged
    set icon size of opts to 128
    set position of item "${APP_NAME}" of container window to {220, 300}
    set position of item "Applications" of container window to {820, 300}
    close
    open
    update without registering applications
    delay 2
  end tell
end tell
EOF

sync
hdiutil detach "$DEVICE"

hdiutil convert "$TMP_DMG" -format UDZO -imagekey zlib-level=9 -o "$OUT_DMG"
rm -f "$TMP_DMG"

echo ""
echo "DMG 생성 완료: $OUT_DMG"
