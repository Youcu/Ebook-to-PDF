import os
import shutil
import tempfile
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import img2pdf
import pyautogui
from PIL import Image
import PIL.JpegImagePlugin  # noqa: F401
import PIL.PdfImagePlugin  # noqa: F401
import PIL.PngImagePlugin  # noqa: F401
from PySide6.QtCore import QThread, Signal

try:
    import Quartz
except Exception:  # pragma: no cover - platform dependent import
    Quartz = None


INVALID_FILENAME_CHARS = '/\\:*?"<>|'


@dataclass
class CaptureConfig:
    region: Dict[str, int]
    focus_point: Tuple[int, int]
    total_pages: int
    speed: float
    pdf_name: str
    save_dir: str


class CaptureWorker(QThread):
    progress_changed = Signal(int)
    status_changed = Signal(str)
    finished_success = Signal(str)
    failed = Signal(str)

    def __init__(self, config: CaptureConfig):
        super().__init__()
        self.config = config
        self._stop_event = threading.Event()

    def request_stop(self) -> None:
        self._stop_event.set()

    def _stop_requested(self) -> bool:
        return self._stop_event.is_set()

    def _validate_config(self) -> None:
        required_keys = {"top", "left", "width", "height"}
        if not required_keys.issubset(set(self.config.region.keys())):
            raise ValueError("Region must include top, left, width, height.")

        width = int(self.config.region["width"])
        height = int(self.config.region["height"])
        if width <= 0 or height <= 0:
            raise ValueError("Capture width/height must be greater than 0.")

        if int(self.config.total_pages) < 1:
            raise ValueError("Total pages must be at least 1.")

        if float(self.config.speed) < 0:
            raise ValueError("Speed must be >= 0.")

        if not self.config.pdf_name.strip():
            raise ValueError("PDF name is required.")

        if not self.config.save_dir.strip():
            raise ValueError("Save directory is required.")

    def _sanitize_pdf_name(self, name: str) -> str:
        sanitized = "".join(
            "_" if ch in INVALID_FILENAME_CHARS else ch for ch in name.strip()
        ).strip()
        sanitized = sanitized.rstrip(".")
        return sanitized or "ebook_capture"

    def _send_next_page_key(self) -> None:
        pyautogui.press("right")

    def _capture_region_quartz(self, region: Dict[str, int], output_path: str) -> bool:
        if Quartz is None:
            return False

        left = int(region["left"])
        top = int(region["top"])
        width = int(region["width"])
        height = int(region["height"])

        capture_rect = Quartz.CGRectMake(left, top, width, height)
        image_ref = Quartz.CGWindowListCreateImage(
            capture_rect,
            Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID,
            Quartz.kCGWindowImageDefault,
        )
        if not image_ref:
            return False

        img_width = Quartz.CGImageGetWidth(image_ref)
        img_height = Quartz.CGImageGetHeight(image_ref)
        bytes_per_row = Quartz.CGImageGetBytesPerRow(image_ref)
        data_provider = Quartz.CGImageGetDataProvider(image_ref)
        if data_provider is None:
            return False
        raw_data = Quartz.CGDataProviderCopyData(data_provider)
        if raw_data is None:
            return False

        image = Image.frombuffer(
            "RGBA",
            (img_width, img_height),
            bytes(raw_data),
            "raw",
            "BGRA",
            bytes_per_row,
            1,
        )
        image.save(output_path, format="PNG")
        return True

    def _capture_region(self, region: Dict[str, int], output_path: str) -> None:
        if self._capture_region_quartz(region, output_path):
            return
        raise RuntimeError("No capture backend available (Quartz unavailable).")

    def run(self) -> None:
        temp_dir = None

        try:
            self._validate_config()
            os.makedirs(self.config.save_dir, exist_ok=True)

            pdf_stem = self._sanitize_pdf_name(self.config.pdf_name)
            pdf_path = os.path.join(self.config.save_dir, f"{pdf_stem}.pdf")
            temp_dir = tempfile.mkdtemp(prefix="ebook_to_pdf_")

            interaction_region = {
                "top": int(self.config.region["top"]),
                "left": int(self.config.region["left"]),
                "width": int(self.config.region["width"]),
                "height": int(self.config.region["height"]),
            }

            self.status_changed.emit("전자책 창 활성화 중...")
            pyautogui.click(
                int(self.config.focus_point[0]) + 10,
                int(self.config.focus_point[1]) + 10,
            )
            initial_settle = max(float(self.config.speed), 0.1)
            time.sleep(initial_settle)

            image_paths = []
            for page in range(1, int(self.config.total_pages) + 1):
                if self._stop_requested():
                    raise RuntimeError("Capture stopped by user")

                self.status_changed.emit(
                    f"{page}/{self.config.total_pages} 페이지 캡처 중..."
                )

                image_path = os.path.join(temp_dir, f"img_{page:05d}.png")
                self._capture_region(interaction_region, image_path)
                image_paths.append(image_path)

                progress = int((page / int(self.config.total_pages)) * 100)
                self.progress_changed.emit(progress)

                if page < int(self.config.total_pages):
                    self._send_next_page_key()
                    render_settle = max(float(self.config.speed), 0.1)
                    time.sleep(render_settle)

            if not image_paths:
                raise RuntimeError("No images were captured.")

            self.status_changed.emit("PDF 생성 중...")
            with open(pdf_path, "wb") as pdf_file:
                pdf_file.write(img2pdf.convert(image_paths))

            self.progress_changed.emit(100)
            self.status_changed.emit("완료")
            self.finished_success.emit(pdf_path)
        except Exception as exc:
            self.failed.emit(repr(exc))
        finally:
            if temp_dir and os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
