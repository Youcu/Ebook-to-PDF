#!/bin/zsh
# 과거 빌드가 TCC 권한 DB에 남겨 둔 잔존 항목을 제거합니다.
# ad-hoc 서명은 재빌드마다 신원(cdhash)이 바뀌어 새 빌드가 과거 항목에 막히므로,
# 재빌드 후 권한이 풀리면 이 스크립트로 항목을 제거한 뒤 앱을 다시 실행해 권한을 새로 승인하면 됩니다.
set -uo pipefail

# 번들 식별자: EbookToPDF.spec 의 bundle_identifier 와 동일해야 합니다.
BUNDLE_ID="com.local.ebooktopdf"

# 이 앱이 실제로 사용하는 권한 서비스만 리셋합니다.
#   ScreenCapture  : 화면 기록 (Quartz 캡처)
#   Accessibility  : 자동 클릭/키 입력 (pyautogui)
#   ListenEvent    : 입력 모니터링 (pynput 좌표 클릭 리스너)
for svc in ScreenCapture Accessibility ListenEvent; do
  echo "Resetting ${svc} for ${BUNDLE_ID}..."
  # 해당 항목이 없으면 tccutil 이 non-zero 를 반환할 수 있으므로 무시합니다.
  tccutil reset "$svc" "$BUNDLE_ID" || true
done

echo ""
echo "권한 항목 리셋 완료. 앱을 다시 실행하면 권한을 새로 요청합니다."
