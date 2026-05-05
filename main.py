import os
import subprocess
import sys
from typing import Optional, Tuple

import pyautogui
from pynput import mouse
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from capture_worker import CaptureConfig, CaptureWorker
from permission_utils import (
    get_app_display_name,
    get_permission_status,
    is_macos,
    open_accessibility_settings,
    open_input_monitoring_settings,
    open_privacy_security_settings,
    open_screen_recording_settings,
    request_accessibility_permission,
    request_screen_recording_permission,
)

class PermissionWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("EbookToPDF 권한 확인")
        self.setFixedSize(640, 520)
        self.main_window: Optional[MainWindow] = None

        self.screen_preflight_status = QLabel("")
        self.screen_capture_test_status = QLabel("")
        self.accessibility_status = QLabel("")
        self.final_status = QLabel("")

        self.request_screen_button = QPushButton("Screen Recording 권한 요청")
        self.request_accessibility_button = QPushButton("Accessibility 권한 요청")
        self.open_screen_settings_button = QPushButton("Screen Recording 설정 열기")
        self.open_accessibility_settings_button = QPushButton("Accessibility 설정 열기")
        self.open_input_monitoring_settings_button = QPushButton(
            "Input Monitoring 설정 열기"
        )
        self.open_privacy_settings_button = QPushButton("Privacy & Security 설정 열기")
        self.refresh_button = QPushButton("권한 다시 확인")
        self.start_button = QPushButton("MainWindow 시작")
        for button in (
            self.request_screen_button,
            self.request_accessibility_button,
            self.open_screen_settings_button,
            self.open_accessibility_settings_button,
            self.open_input_monitoring_settings_button,
            self.open_privacy_settings_button,
            self.refresh_button,
            self.start_button,
        ):
            button.setFixedHeight(34)

        self.request_screen_button.clicked.connect(self.request_screen_permission)
        self.request_accessibility_button.clicked.connect(
            self.request_accessibility_permission
        )
        self.open_screen_settings_button.clicked.connect(
            open_screen_recording_settings
        )
        self.open_accessibility_settings_button.clicked.connect(
            open_accessibility_settings
        )
        self.open_input_monitoring_settings_button.clicked.connect(
            open_input_monitoring_settings
        )
        self.open_privacy_settings_button.clicked.connect(
            open_privacy_security_settings
        )
        self.refresh_button.clicked.connect(self.refresh_status)
        self.start_button.clicked.connect(self.open_main_window)

        status_group = QGroupBox("현재 권한 상태")
        status_layout = QVBoxLayout()
        status_layout.setSpacing(6)
        status_layout.addWidget(self.screen_preflight_status)
        status_layout.addWidget(self.screen_capture_test_status)
        status_layout.addWidget(self.accessibility_status)
        status_layout.addWidget(self.final_status)
        status_group.setLayout(status_layout)

        info_label = QLabel(
            "\n".join(
                [
                    f"- 이 앱이 {get_app_display_name()} 이름으로 권한 목록에 보이는지 확인해 주세요.",
                    "- 화면 캡처 권한이 허용되어야 페이지를 정확히 저장할 수 있습니다.",
                    "- 손쉬운 사용(Accessibility) 권한이 있어야 자동 페이지 넘김이 동작합니다.",
                    "- 좌표 클릭 지정이 동작하지 않으면 Input Monitoring 권한을 허용해 주세요.",
                    "- 권한 변경 후에는 앱을 완전히 종료한 뒤 다시 실행해 주세요.",
                ]
            )
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: rgba(242, 242, 247, 0.90);")

        button_layout = QVBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addWidget(self.request_screen_button)
        button_layout.addWidget(self.request_accessibility_button)
        button_layout.addWidget(self.open_screen_settings_button)
        button_layout.addWidget(self.open_accessibility_settings_button)
        button_layout.addWidget(self.open_input_monitoring_settings_button)
        button_layout.addWidget(self.open_privacy_settings_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.start_button)

        root_layout = QVBoxLayout()
        root_layout.setSpacing(10)
        root_layout.addWidget(status_group)
        root_layout.addWidget(info_label)
        root_layout.addLayout(button_layout)
        self.setLayout(root_layout)

        self.refresh_status()

    def refresh_status(self) -> None:
        status = get_permission_status()

        self.screen_preflight_status.setText(
            "Screen Recording API 상태: 허용됨"
            if status.screen_recording_preflight
            else "Screen Recording API 상태: 확인 불안정"
        )
        self.screen_capture_test_status.setText(
            "실제 화면 캡처 테스트: 성공"
            if status.screen_recording_capture_test
            else "실제 화면 캡처 테스트: 실패"
        )
        self.accessibility_status.setText(
            "Accessibility: 허용됨"
            if status.accessibility
            else "Accessibility: 필요함"
        )
        self.final_status.setText(
            "최종 실행 가능 상태: 가능"
            if status.all_required_granted
            else "최종 실행 가능 상태: 불가능"
        )

        if is_macos():
            self.start_button.setEnabled(status.all_required_granted)
        else:
            self.start_button.setEnabled(True)

    def request_screen_permission(self) -> None:
        request_screen_recording_permission()
        self.refresh_status()

    def request_accessibility_permission(self) -> None:
        request_accessibility_permission()
        self.refresh_status()

    def open_main_window(self) -> None:
        if is_macos():
            status = get_permission_status()
            if not status.all_required_granted:
                QMessageBox.warning(
                    self,
                    "권한 필요",
                    "필수 권한이 모두 충족되어야 MainWindow를 시작할 수 있습니다.",
                )
                self.refresh_status()
                return

        self.main_window = MainWindow()
        self.main_window.show()
        self.close()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Transform E-Book To PDF")
        self.setFixedSize(520, 540)

        self.top_left: Optional[Tuple[int, int]] = None
        self.bottom_right: Optional[Tuple[int, int]] = None
        self.worker: Optional[CaptureWorker] = None
        self.last_pdf_path: Optional[str] = None

        title = QLabel("Transform E-Book To PDF")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = title.font()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)

        self.left_top_value = QLabel("(0, 0)")
        self.right_bottom_value = QLabel("(0, 0)")
        self.capture_lu_button = QPushButton("Click Position")
        self.capture_rd_button = QPushButton("Click Position")
        self.capture_lu_button.clicked.connect(lambda: self._capture_position_by_click("lu"))
        self.capture_rd_button.clicked.connect(lambda: self._capture_position_by_click("rd"))

        self.total_pages_edit = QLineEdit()
        self.total_pages_edit.setPlaceholderText(" Input Total Pages.")
        self.pdf_name_edit = QLineEdit()
        self.pdf_name_edit.setPlaceholderText(" Input PDF Name.")

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(20)
        self.speed_slider.setValue(5)
        self.speed_slider.valueChanged.connect(self._update_speed_label)
        self.speed_label = QLabel("")
        self._update_speed_label()
        self.speed_help_label = QLabel(
            "0.1 sec는 빠르지만 안정성이 떨어질 수 있습니다."
        )
        self.speed_help_label.setStyleSheet(
            "color: rgba(242, 242, 247, 0.65); font-size: 11px;"
        )

        self.personal_use_checkbox = QCheckBox(
            "개인 소장 목적(저작권법 범위 내)으로만 사용합니다."
        )
        self.capture_lock_notice = QLabel(
            "캡처 중에는 마우스/키보드 조작을 금지하세요. (결과 품질 저하 방지)"
        )
        self.capture_lock_notice.setStyleSheet("color: #ff5f57; font-size: 11px;")
        self.capture_lock_notice.setVisible(False)

        self.create_button = QPushButton("Create PDF")
        self.stop_button = QPushButton("Stop")
        self.init_button = QPushButton("Initialization")
        self.create_button.setFixedSize(470, 50)
        self.stop_button.setEnabled(False)
        self.stop_button.setVisible(False)

        self.create_button.clicked.connect(self._on_primary_button_clicked)
        self.stop_button.clicked.connect(self.stop_capture)
        self.init_button.clicked.connect(self.initialization)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(14)
        self.progress_label = QLabel("0%")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_font = self.status_label.font()
        status_font.setPointSize(13)
        status_font.setBold(True)
        self.status_label.setFont(status_font)

        self.sign_label = QLabel("Made By EastShine, Modified By Hooby")
        sign_font = self.sign_label.font()
        sign_font.setPointSize(9)
        sign_font.setItalic(True)
        self.sign_label.setFont(sign_font)
        self.sign_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        label_lu = QLabel("Image Top Left Corner Position (x,y)\t\t")
        label_rd = QLabel("Image Down Right Corner Position (x,y)\t")
        label_total_pages = QLabel("Total Pages\t\t")
        label_pdf_name = QLabel("PDF Name\t\t")

        box_lu = QHBoxLayout()
        box_lu.setSpacing(8)
        box_lu.addWidget(label_lu)
        box_lu.addWidget(self.left_top_value)
        box_lu.addWidget(self.capture_lu_button)

        box_rd = QHBoxLayout()
        box_rd.setSpacing(8)
        box_rd.addWidget(label_rd)
        box_rd.addWidget(self.right_bottom_value)
        box_rd.addWidget(self.capture_rd_button)

        box_total_pages = QHBoxLayout()
        box_total_pages.setSpacing(8)
        box_total_pages.addWidget(label_total_pages)
        box_total_pages.addWidget(self.total_pages_edit)

        box_pdf_name = QHBoxLayout()
        box_pdf_name.setSpacing(8)
        box_pdf_name.addWidget(label_pdf_name)
        box_pdf_name.addWidget(self.pdf_name_edit)

        speed_row = QHBoxLayout()
        speed_row.setSpacing(10)
        speed_row.addWidget(self.speed_label)
        speed_row.addWidget(self.speed_slider)

        init_row = QHBoxLayout()
        init_row.setSpacing(8)
        init_row.addWidget(self.init_button)
        init_row.addStretch(1)
        init_row.addWidget(self.stop_button)
        init_row.addWidget(self.sign_label)

        progress_row = QHBoxLayout()
        progress_row.setSpacing(10)
        progress_row.addWidget(self.progress_bar)
        progress_row.addWidget(self.progress_label)

        status_row = QHBoxLayout()
        status_row.addWidget(self.status_label)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(16, 14, 16, 16)
        root_layout.setSpacing(10)
        root_layout.addWidget(title)
        root_layout.addSpacing(12)
        root_layout.addLayout(box_lu)
        root_layout.addSpacing(2)
        root_layout.addLayout(box_rd)
        root_layout.addSpacing(2)
        root_layout.addLayout(box_total_pages)
        root_layout.addLayout(box_pdf_name)
        root_layout.addSpacing(4)
        root_layout.addLayout(speed_row)
        root_layout.addWidget(self.speed_help_label)
        root_layout.addSpacing(2)
        root_layout.addWidget(self.personal_use_checkbox)
        root_layout.addWidget(self.capture_lock_notice)
        root_layout.addSpacing(2)
        root_layout.addLayout(init_row)
        root_layout.addLayout(progress_row)
        root_layout.addLayout(status_row)
        root_layout.addSpacing(8)
        root_layout.addWidget(self.create_button, alignment=Qt.AlignmentFlag.AlignCenter)

        container = QWidget()
        container.setLayout(root_layout)
        self.setCentralWidget(container)

    def _on_primary_button_clicked(self) -> None:
        if self.last_pdf_path:
            self.open_generated_pdf()
            return
        self.start_capture()

    def open_generated_pdf(self) -> None:
        if not self.last_pdf_path or not os.path.isfile(self.last_pdf_path):
            QMessageBox.warning(
                self,
                "파일 없음",
                "생성된 PDF를 찾을 수 없습니다. 다시 생성해 주세요.",
            )
            self.last_pdf_path = None
            self.create_button.setText("Create PDF")
            return

        try:
            pdf_dir = os.path.dirname(self.last_pdf_path)
            subprocess.run(["open", pdf_dir], check=False)
            subprocess.run(["open", "-R", self.last_pdf_path], check=False)
            self._set_status(f"PDF 열기: {self.last_pdf_path}")
        except Exception as exc:
            QMessageBox.critical(self, "오류", f"PDF 열기 실패: {repr(exc)}")

    def _update_speed_label(self) -> None:
        speed = self.speed_slider.value() / 10.0
        self.speed_label.setText(f"Capture Speed : {speed:.1f}sec")

    def _capture_position_by_click(self, target: str) -> None:
        if self.worker and self.worker.isRunning():
            self._set_status("캡처 실행 중에는 좌표를 변경할 수 없습니다.")
            return
        target_name = "좌상단" if target == "lu" else "우하단"
        self._set_status(f"{target_name} 좌표를 저장하려면 원하는 위치를 클릭하세요.")

        try:
            clicked_point: Optional[Tuple[int, int]] = None

            def on_click(x, y, button, pressed):
                nonlocal clicked_point
                if pressed:
                    clicked_point = (int(x), int(y))
                    return False
                return True

            with mouse.Listener(on_click=on_click) as listener:
                listener.join()

            if clicked_point is None:
                self._set_status("좌표 저장이 취소되었습니다.")
                return

            if target == "lu":
                self.top_left = clicked_point
                self.left_top_value.setText(f"({clicked_point[0]}, {clicked_point[1]})")
                self._set_status("좌상단 좌표가 저장되었습니다.")
            else:
                self.bottom_right = clicked_point
                self.right_bottom_value.setText(
                    f"({clicked_point[0]}, {clicked_point[1]})"
                )
                self._set_status("우하단 좌표가 저장되었습니다.")
        except Exception as exc:
            self._set_status(
                f"좌표 저장 실패: {repr(exc)} (Input Monitoring/Accessibility 설정 확인)"
            )

    def _validate_before_capture(self) -> Optional[CaptureConfig]:
        if is_macos():
            permission_status = get_permission_status()
            if not permission_status.accessibility:
                QMessageBox.warning(
                    self,
                    "Accessibility 필요",
                    "Accessibility 권한이 없어 자동 클릭/키 입력을 수행할 수 없습니다.",
                )
                return None
            if not permission_status.screen_recording:
                QMessageBox.warning(
                    self,
                    "Screen Recording 필요",
                    "실제 캡처/권한 상태를 확인한 결과 Screen Recording 사용이 불가능합니다.",
                )
                return None

        if self.top_left is None or self.bottom_right is None:
            QMessageBox.warning(self, "좌표 필요", "좌상단/우하단 좌표를 먼저 지정하세요.")
            return None

        if self.bottom_right[0] <= self.top_left[0] or self.bottom_right[1] <= self.top_left[1]:
            QMessageBox.warning(
                self,
                "좌표 오류",
                "우하단 좌표는 좌상단 좌표보다 오른쪽 아래여야 합니다.",
            )
            return None

        try:
            total_pages = int(self.total_pages_edit.text().strip())
        except ValueError:
            QMessageBox.warning(self, "입력 오류", "총 페이지 수는 정수로 입력해야 합니다.")
            return None

        if total_pages < 1:
            QMessageBox.warning(self, "입력 오류", "총 페이지 수는 1 이상이어야 합니다.")
            return None

        pdf_name = self.pdf_name_edit.text().strip()
        if not pdf_name:
            QMessageBox.warning(self, "입력 오류", "PDF 이름을 입력해야 합니다.")
            return None

        if not self.personal_use_checkbox.isChecked():
            QMessageBox.warning(
                self,
                "확인 필요",
                "개인 소장 확인 체크박스를 선택해야 진행할 수 있습니다.",
            )
            return None

        speed = self.speed_slider.value() / 10.0
        region = {
            "left": int(self.top_left[0]),
            "top": int(self.top_left[1]),
            "width": int(self.bottom_right[0] - self.top_left[0]),
            "height": int(self.bottom_right[1] - self.top_left[1]),
        }
        save_dir = os.path.expanduser("~/MyEbooks")

        return CaptureConfig(
            region=region,
            focus_point=(int(self.top_left[0]), int(self.top_left[1])),
            total_pages=total_pages,
            speed=speed,
            pdf_name=pdf_name,
            save_dir=save_dir,
        )

    def _set_running_state(self, running: bool) -> None:
        self.create_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.stop_button.setVisible(running)
        self.init_button.setEnabled(not running)
        self.capture_lu_button.setEnabled(not running)
        self.capture_rd_button.setEnabled(not running)
        self.capture_lock_notice.setVisible(running)

    def start_capture(self) -> None:
        if self.worker and self.worker.isRunning():
            self._set_status("이미 캡처가 실행 중입니다.")
            return

        config = self._validate_before_capture()
        if config is None:
            return

        self.last_pdf_path = None
        self.create_button.setText("Create PDF")
        self.progress_bar.setValue(0)
        self.progress_label.setText("0%")
        self._set_running_state(True)
        self._set_status("캡처를 시작합니다.")

        self.worker = CaptureWorker(config)
        self.worker.progress_changed.connect(self._set_progress_value)
        self.worker.status_changed.connect(self._set_status)
        self.worker.finished_success.connect(self._on_capture_finished)
        self.worker.failed.connect(self._on_capture_failed)
        self.worker.finished.connect(self._on_worker_finished)
        self.worker.start()

    def stop_capture(self) -> None:
        if self.worker and self.worker.isRunning():
            self.worker.request_stop()
            self.stop_button.setEnabled(False)
            self._set_status("중단 요청 중...")

    def _on_capture_finished(self, pdf_path: str) -> None:
        self.last_pdf_path = pdf_path
        self.create_button.setText("Open PDF")
        self._set_status(f"완료: {pdf_path}")
        QMessageBox.information(
            self,
            "완료",
            f"PDF 생성이 완료되었습니다.\n{pdf_path}",
        )

    def _on_capture_failed(self, error_text: str) -> None:
        if "Capture stopped by user" in error_text:
            self._set_status("사용자 요청으로 중단되었습니다.")
            return

        self._set_status(f"오류: {error_text}")
        QMessageBox.critical(self, "오류", error_text)

    def _on_worker_finished(self) -> None:
        self._set_running_state(False)
        self.worker = None

    def initialization(self) -> None:
        if self.worker and self.worker.isRunning():
            self._set_status("캡처 실행 중에는 초기화할 수 없습니다.")
            return

        self.top_left = None
        self.bottom_right = None
        self.left_top_value.setText("(0, 0)")
        self.right_bottom_value.setText("(0, 0)")
        self.total_pages_edit.clear()
        self.pdf_name_edit.clear()
        self.last_pdf_path = None
        self.create_button.setText("Create PDF")
        self.speed_slider.setValue(5)
        self.personal_use_checkbox.setChecked(False)
        self.progress_bar.setValue(0)
        self.progress_label.setText("0%")
        self._set_status("")

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def _set_progress_value(self, value: int) -> None:
        self.progress_bar.setValue(value)
        self.progress_label.setText(f"{value}%")

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "종료 확인",
                "캡처 실행 중입니다. 종료하면 작업이 중단됩니다. 종료하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

            self.worker.request_stop()
            self.worker.wait(3000)

        event.accept()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("EbookToPDF")
    if is_macos() and get_permission_status().all_required_granted:
        window = MainWindow()
    else:
        window = PermissionWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
