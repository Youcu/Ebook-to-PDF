import ctypes
import os
import platform
import subprocess
import sys
from dataclasses import dataclass

try:
    import Quartz
except Exception:  # pragma: no cover - platform dependent import
    Quartz = None


@dataclass
class PermissionStatus:
    screen_recording_preflight: bool
    screen_recording_capture_test: bool
    accessibility: bool

    @property
    def screen_recording(self) -> bool:
        return self.screen_recording_capture_test or self.screen_recording_preflight

    @property
    def all_required_granted(self) -> bool:
        return self.screen_recording and self.accessibility


def is_macos() -> bool:
    return platform.system() == "Darwin"


def get_app_display_name() -> str:
    if not is_macos():
        return "EbookToPDF"

    executable = os.path.abspath(sys.executable)
    marker = ".app/Contents/MacOS/"
    if marker in executable:
        app_root = executable.split(marker, 1)[0]
        return f"{os.path.basename(app_root)}.app"

    base = os.path.basename(executable) or "EbookToPDF"
    if base.endswith(".app"):
        return base
    if base.lower().startswith("python"):
        return "EbookToPDF.app"
    return f"{base}.app"


def check_screen_recording_preflight() -> bool:
    if not is_macos():
        return True

    try:
        core_graphics = ctypes.CDLL(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        preflight = core_graphics.CGPreflightScreenCaptureAccess
        preflight.restype = ctypes.c_bool
        preflight.argtypes = []
        return bool(preflight())
    except Exception:
        return False


def request_screen_recording_permission() -> bool:
    if not is_macos():
        return True

    try:
        core_graphics = ctypes.CDLL(
            "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        request = core_graphics.CGRequestScreenCaptureAccess
        request.restype = ctypes.c_bool
        request.argtypes = []
        return bool(request())
    except Exception:
        return False


def check_screen_recording_by_real_capture() -> bool:
    if not is_macos():
        return True

    try:
        if Quartz is None:
            return False

        capture_rect = Quartz.CGRectMake(0, 0, 10, 10)
        image_ref = Quartz.CGWindowListCreateImage(
            capture_rect,
            Quartz.kCGWindowListOptionOnScreenOnly,
            Quartz.kCGNullWindowID,
            Quartz.kCGWindowImageDefault,
        )
        if not image_ref:
            return False

        width = Quartz.CGImageGetWidth(image_ref)
        height = Quartz.CGImageGetHeight(image_ref)
        return bool(width > 0 and height > 0)
    except Exception:
        return False


def check_accessibility_permission(prompt: bool = False) -> bool:
    if not is_macos():
        return True

    try:
        import ApplicationServices

        options = {
            ApplicationServices.kAXTrustedCheckOptionPrompt: bool(prompt),
        }
        if hasattr(ApplicationServices, "AXIsProcessTrustedWithOptions"):
            return bool(
                ApplicationServices.AXIsProcessTrustedWithOptions(options)
            )
        if hasattr(ApplicationServices, "AXIsProcessTrusted"):
            return bool(ApplicationServices.AXIsProcessTrusted())
        return False
    except Exception:
        return False


def request_accessibility_permission() -> bool:
    return check_accessibility_permission(prompt=True)


def get_permission_status() -> PermissionStatus:
    return PermissionStatus(
        screen_recording_preflight=check_screen_recording_preflight(),
        screen_recording_capture_test=check_screen_recording_by_real_capture(),
        accessibility=check_accessibility_permission(prompt=False),
    )


def open_screen_recording_settings() -> None:
    subprocess.run(
        [
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture",
        ],
        check=False,
    )


def open_accessibility_settings() -> None:
    subprocess.run(
        [
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility",
        ],
        check=False,
    )


def open_privacy_security_settings() -> None:
    subprocess.run(
        ["open", "x-apple.systempreferences:com.apple.preference.security"],
        check=False,
    )


def open_input_monitoring_settings() -> None:
    subprocess.run(
        [
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent",
        ],
        check=False,
    )
