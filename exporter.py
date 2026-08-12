"""Writers for Windows CUR, ANI and installable cursor packs."""
from __future__ import annotations

import io
import re
import struct
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(slots=True)
class CursorFrame:
    image: Image.Image
    hotspot: tuple[int, int] = (0, 0)
    duration_ms: int = 100


def _dib_bytes(image: Image.Image) -> bytes:
    """Encode a legacy-compatible 32-bit cursor DIB plus its 1-bit AND mask."""
    rgba = image.convert("RGBA")
    width, height = rgba.size
    xor_rows: list[bytes] = []
    mask_rows: list[bytes] = []
    mask_stride = ((width + 31) // 32) * 4
    for y in range(height - 1, -1, -1):
        xor_row = bytearray()
        mask_row = bytearray(mask_stride)
        for x in range(width):
            red, green, blue, alpha = rgba.getpixel((x, y))
            xor_row.extend((blue, green, red, alpha))
            if alpha == 0:
                mask_row[x // 8] |= 0x80 >> (x % 8)
        xor_rows.append(bytes(xor_row))
        mask_rows.append(bytes(mask_row))
    xor_bitmap = b"".join(xor_rows)
    and_mask = b"".join(mask_rows)
    header = struct.pack(
        "<IiiHHIIiiII",
        40,
        width,
        height * 2,
        1,
        32,
        0,
        len(xor_bitmap) + len(and_mask),
        0,
        0,
        0,
        0,
    )
    return header + xor_bitmap + and_mask


def build_cur(frame: CursorFrame) -> bytes:
    image = frame.image.convert("RGBA")
    if not (1 <= image.width <= 256 and 1 <= image.height <= 256):
        raise ValueError("CUR chỉ hỗ trợ kích thước từ 1 đến 256 pixel.")
    hot_x = min(max(int(frame.hotspot[0]), 0), image.width - 1)
    hot_y = min(max(int(frame.hotspot[1]), 0), image.height - 1)
    payload = _dib_bytes(image)
    header = struct.pack("<HHH", 0, 2, 1)
    entry = struct.pack(
        "<BBBBHHII",
        image.width if image.width < 256 else 0,
        image.height if image.height < 256 else 0,
        0,
        0,
        hot_x,
        hot_y,
        len(payload),
        22,
    )
    return header + entry + payload


def export_cur(path: str | Path, frame: CursorFrame) -> None:
    Path(path).write_bytes(build_cur(frame))


def _chunk(tag: bytes, payload: bytes) -> bytes:
    return tag + struct.pack("<I", len(payload)) + payload + (b"\0" if len(payload) % 2 else b"")


def build_ani(frames: list[CursorFrame]) -> bytes:
    if not frames:
        raise ValueError("ANI cần ít nhất một frame.")
    width = max(frame.image.width for frame in frames)
    height = max(frame.image.height for frame in frames)
    rates = [max(1, round(frame.duration_ms * 60 / 1000)) for frame in frames]
    # cbSize, nFrames, nSteps, width, height, bitcount, planes, default rate, flags.
    anih = struct.pack("<9I", 36, len(frames), len(frames), width, height, 32, 1, rates[0], 3)
    fram = b"fram" + b"".join(_chunk(b"icon", build_cur(frame)) for frame in frames)
    body = b"ACON" + _chunk(b"anih", anih) + _chunk(b"rate", struct.pack(f"<{len(rates)}I", *rates))
    body += _chunk(b"seq ", struct.pack(f"<{len(frames)}I", *range(len(frames))))
    body += _chunk(b"LIST", fram)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def parse_ani(data: bytes) -> tuple[list[Image.Image], tuple[int, int], list[int]]:
    """Đọc file .ani (RIFF/ACON) -> (các frame RGBA, hotspot, rates theo 1/60 giây)."""
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != b"ACON":
        raise ValueError("Không phải file ANI hợp lệ.")
    frames: list[Image.Image] = []
    hotspot = (0, 0)
    rates: list[int] = []
    default_rate = 5
    pos = 12
    end = len(data)
    while pos + 8 <= end:
        cid = data[pos : pos + 4]
        size = struct.unpack_from("<I", data, pos + 4)[0]
        body_start = pos + 8
        body_end = body_start + size + (size & 1)
        if body_end > end:
            break
        if cid == b"anih":
            if size >= 36:
                default_rate = struct.unpack_from("<I", data, body_start + 24)[0]
        elif cid == b"rate":
            count = size // 4
            rates = list(struct.unpack_from(f"<{count}I", data, body_start))
        elif cid == b"LIST":
            if data[body_start : body_start + 4] == b"fram":
                p = body_start + 4
                while p + 8 <= body_end:
                    sub_id = data[p : p + 4]
                    sub_size = struct.unpack_from("<I", data, p + 4)[0]
                    sub_start = p + 8
                    if sub_id == b"icon":
                        icon_data = data[sub_start : sub_start + sub_size]
                        frames.append(Image.open(io.BytesIO(icon_data)).convert("RGBA"))
                        if len(icon_data) >= 22 and icon_data[2:4] == b"\x02\x00":
                            x_hot = struct.unpack_from("<H", icon_data, 10)[0]
                            y_hot = struct.unpack_from("<H", icon_data, 12)[0]
                            hotspot = (x_hot, y_hot)
                    p = sub_start + sub_size + (sub_size & 1)
        pos = body_end
    if not frames:
        raise ValueError("ANI không chứa frame nào.")
    if not rates:
        rates = [default_rate] * len(frames)
    return frames, hotspot, rates


def export_ani(path: str | Path, frames: list[CursorFrame]) -> None:
    Path(path).write_bytes(build_ani(frames))


def safe_pack_name(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]', "", name).strip().rstrip(".")
    return cleaned or "Pixel Cursor Pack"


def build_install_inf(scheme_name: str, assignments: dict[str, str]) -> str:
    folder = safe_pack_name(scheme_name)
    escaped = scheme_name.replace('"', '\\"')
    lines = [
        "; Generated by Benj Cursor Maker",
        "[Version]",
        'Signature="$Windows NT$"',
        "",
        "[DefaultInstall]",
        "CopyFiles=Cursor.Files",
        "AddReg=Cursor.Reg",
        "",
        "[DefaultInstall.NT]",
        "CopyFiles=Cursor.Files",
        "AddReg=Cursor.Reg",
        "",
        "[DestinationDirs]",
        f'Cursor.Files=10,"Cursors\\{folder}"',
        "",
        "[Cursor.Files]",
    ]
    filenames = list(dict.fromkeys(Path(value).name for value in assignments.values()))
    lines.extend(filenames)
    lines += ["", "[Cursor.Reg]"]
    scheme_values: list[str] = []
    windows_roles = [
        "Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", "NWPen",
        "No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", "SizeAll", "UpArrow", "Hand",
    ]
    for role in windows_roles:
        filename = Path(assignments[role]).name if role in assignments else ""
        scheme_values.append(f"%10%\\Cursors\\{folder}\\{filename}" if filename else "")
        if filename:
            lines.append(
                f'HKCU,"Control Panel\\Cursors",{role},0x00000000,"%10%\\Cursors\\{folder}\\{filename}"'
            )
    scheme_csv = ",".join(scheme_values)
    lines.append(f'HKCU,"Control Panel\\Cursors\\Schemes","{escaped}",0x00000000,"{scheme_csv}"')
    lines += ["", "[Strings]", f'PACKNAME="{escaped}"', ""]
    return "\r\n".join(lines)


def build_install_bat(scheme_name: str, assignments: dict[str, str]) -> str:
    """Create a self-elevating installer that installs and activates the scheme."""
    folder = safe_pack_name(scheme_name).replace("%", "").replace("!", "")
    display_name = scheme_name.replace("%", "").replace("!", "").replace('"', "")
    lines = [
        "@echo off",
        "setlocal DisableDelayedExpansion",
        "cd /d \"%~dp0\"",
        # Prologue: tự chạy lại chính mình ở chế độ ẩn (không hiện cửa sổ cmd).
        'if "%~1"=="BCM_HIDDEN" goto :install',
        'set "VBS=%TEMP%\\bcm_hide_%RANDOM%.vbs"',
        '> "%VBS%" echo Set s = CreateObject("WScript.Shell"^)',
        '>> "%VBS%" echo s.Run "cmd /c ""%~f0"" BCM_HIDDEN", 0, False',
        'cscript //nologo "%VBS%" >nul 2>&1',
        'del "%VBS%" >nul 2>&1',
        "exit /b",
        ":install",
        "net session >nul 2>&1",
        "if %errorlevel% neq 0 (",
        '  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath \'%~f0\' -ArgumentList \'BCM_HIDDEN\' -WorkingDirectory \'%~dp0\' -WindowStyle Hidden -Verb RunAs"',
        "  exit /b",
        ")",
        "echo Installing cursor files and Windows scheme...",
        "RUNDLL32.EXE setupapi.dll,InstallHinfSection DefaultInstall 132 \"%~dp0install.inf\"",
        "if errorlevel 1 goto :error",
        f'set "PACK_DIR=%WINDIR%\\Cursors\\{folder}"',
        f'reg add "HKCU\\Control Panel\\Cursors" /ve /t REG_SZ /d "{display_name}" /f >nul',
    ]
    for role, source in assignments.items():
        filename = Path(source).name.replace('"', "")
        lines.append(
            f'reg add "HKCU\\Control Panel\\Cursors" /v "{role}" /t REG_EXPAND_SZ '
            f'/d "%%SystemRoot%%\\Cursors\\{folder}\\{filename}" /f >nul'
        )
    lines += [
        'reg add "HKCU\\Control Panel\\Cursors" /v "Scheme Source" /t REG_DWORD /d 1 /f >nul',
        "RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters",
        "echo.",
        f'echo Installed and activated: {display_name}',
        "echo You can close this window.",
        "timeout /t 3 >nul",
        "exit /b 0",
        ":error",
        "echo.",
        "echo Installation failed. Keep install.bat, install.inf and cursor files in the same folder.",
        "pause",
        "exit /b 1",
        "",
    ]
    return "\r\n".join(lines)


def export_cursorpack_folder(
    parent_dir: str | Path,
    scheme_name: str,
    assignments: dict[str, Path],
    files: dict[Path, bytes] | None = None,
) -> Path:
    """Write an installable cursor pack into a folder named after the scheme.

    The folder contains install.inf, install.bat, README.txt and every cursor
    file, ready to install by double-clicking install.bat — no zip/extract step.
    """
    target = Path(parent_dir) / safe_pack_name(scheme_name)
    target.mkdir(parents=True, exist_ok=True)
    archived = {role: source.name for role, source in assignments.items()}
    (target / "install.inf").write_bytes(build_install_inf(scheme_name, archived).encode("utf-8-sig"))
    (target / "install.bat").write_bytes(build_install_bat(scheme_name, archived).encode("utf-8-sig"))
    for source in dict.fromkeys(assignments.values()):
        payload = files[source] if files and source in files else source.read_bytes()
        (target / source.name).write_bytes(payload)
    (target / "README.txt").write_text(
        "Benj Cursor Maker\r\n\r\nDouble-click install.bat de tu cai va kich hoat cursor scheme.\r\n"
        "Windows se hoi quyen Administrator.\r\n",
        encoding="utf-8",
    )
    return target

