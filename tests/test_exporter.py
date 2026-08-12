import struct
from pathlib import Path

from PIL import Image

from exporter import (
    CursorFrame,
    build_ani,
    build_cur,
    build_install_bat,
    build_install_inf,
    export_cursorpack_folder,
)


def frame(color="red", duration=100, hotspot=(2, 3)):
    return CursorFrame(Image.new("RGBA", (16, 16), color), hotspot, duration)


def test_cur_has_cursor_header_hotspot_and_png_payload():
    data = build_cur(frame())
    reserved, kind, count = struct.unpack_from("<HHH", data)
    width, height, _, _, hot_x, hot_y, size, offset = struct.unpack_from("<BBBBHHII", data, 6)
    assert (reserved, kind, count) == (0, 2, 1)
    assert (width, height, hot_x, hot_y, offset) == (16, 16, 2, 3, 22)
    dib_size, dib_width, dib_height, planes, bit_count = struct.unpack_from("<IiiHH", data, offset)
    assert (dib_size, dib_width, dib_height, planes, bit_count) == (40, 16, 32, 1, 32)
    assert len(data[offset:]) == size


def test_cur_dib_has_bottom_up_bgra_pixels_and_dword_aligned_and_mask():
    image = Image.new("RGBA", (3, 2), (0, 0, 0, 0))
    image.putpixel((0, 0), (255, 0, 0, 255))
    image.putpixel((2, 1), (0, 255, 0, 255))
    data = build_cur(CursorFrame(image, (0, 0), 100))
    payload = data[22:]
    xor = payload[40 : 40 + 3 * 2 * 4]
    mask = payload[40 + 3 * 2 * 4 :]
    assert xor[:4] == bytes((0, 0, 0, 0))  # bottom-left transparent pixel
    assert xor[8:12] == bytes((0, 255, 0, 255))  # bottom-right green, BGRA
    assert xor[12:16] == bytes((0, 0, 255, 255))  # top-left red, BGRA
    assert len(mask) == 8  # 2 rows, each DWORD aligned
    assert mask[:4] == bytes((0b11000000, 0, 0, 0))


def test_ani_is_riff_acon_with_two_icon_frames():
    data = build_ani([frame("red", 100), frame("blue", 200)])
    assert data[:4] == b"RIFF"
    assert data[8:12] == b"ACON"
    assert b"anih" in data
    assert b"rate" in data
    assert b"LIST" in data
    assert data.count(b"icon") == 2
    assert struct.unpack_from("<I", data, 4)[0] == len(data) - 8


def test_install_inf_maps_windows_roles_and_escapes_scheme_name():
    inf = build_install_inf('Neon "Pack"', {"Arrow": "Normal.cur", "IBeam": "Text.cur"})
    assert 'HKCU,"Control Panel\\Cursors",Arrow' in inf
    assert 'HKCU,"Control Panel\\Cursors",IBeam' in inf
    assert 'Neon \\"Pack\\"' in inf
    assert "%10%\\Cursors\\Neon Pack\\Normal.cur" in inf
    assert 'Signature="$Windows NT$"' in inf
    assert "[DefaultInstall.NT]" in inf


def test_parse_ani_roundtrip():
    """build_ani -> parse_ani khôi phục đúng frame, hotspot và tốc độ."""
    from PIL import Image

    from exporter import CursorFrame, build_ani, parse_ani

    frames = [
        CursorFrame(Image.new("RGBA", (16, 16), (255, 0, 0, 255)), (7, 8), 100),
        CursorFrame(Image.new("RGBA", (16, 16), (0, 255, 0, 255)), (7, 8), 200),
    ]
    parsed_frames, hotspot, rates = parse_ani(build_ani(frames))
    assert len(parsed_frames) == 2
    assert parsed_frames[0].size == (16, 16)
    assert parsed_frames[1].getpixel((0, 0)) == (0, 255, 0, 255)
    assert hotspot == (7, 8)
    assert rates == [6, 12]  # 100 ms -> 6 jiffy, 200 ms -> 12 jiffy (1/60 s)


def test_run_bat_hides_console_and_uses_pythonw():
    """run.bat phải tự chạy lại ẩn và khởi động app bằng pythonw (không dính console)."""
    from pathlib import Path

    run_bat = Path(__file__).resolve().parent.parent / "run.bat"
    assert run_bat.exists()
    content = run_bat.read_text(encoding="utf-8", errors="replace")
    assert 'if "%~1"=="BCM_HIDDEN" goto :run' in content
    assert 'Set s = CreateObject("WScript.Shell"^)' in content
    assert "s.Run \"cmd /c \"\"%~f0\"\" BCM_HIDDEN\", 0, False" in content
    assert "pythonw.exe" in content
    # app chạy bằng pythonw THẬT (GUI subsystem, ws=1 -> window hiện, không console) + PYTHONPATH trỏ venv
    assert 's.Run """%PYW%"" main.py", 1, False' in content
    assert 'set "PYTHONPATH=%~dp0.venv\\Lib\\site-packages"' in content
    assert 'findstr /b "home" ".venv\\pyvenv.cfg"' in content
    assert "start \"\"" not in content
    # không còn chạy app bằng python.exe dính console
    assert ".venv\\Scripts\\python.exe main.py" not in content


def test_cursorpack_folder_named_after_scheme_contains_inf_bat_and_cursor(tmp_path):
    target = export_cursorpack_folder(
        tmp_path,
        "Neon",
        {"Arrow": Path("Normal.cur")},
        {Path("Normal.cur"): b"CUR"},
    )
    assert target == tmp_path / "Neon"
    assert (target / "install.inf").exists()
    assert (target / "install.bat").exists()
    assert (target / "README.txt").exists()
    assert (target / "Normal.cur").read_bytes() == b"CUR"
    installer = (target / "install.bat").read_text(encoding="utf-8-sig")
    assert "InstallHinfSection DefaultInstall 132" in installer
    assert "Start-Process" in installer
    assert "-Verb RunAs" in installer
    assert 'reg add "HKCU\\Control Panel\\Cursors" /v "Arrow"' in installer
    assert 'reg add "HKCU\\Control Panel\\Cursors" /v "Scheme Source"' in installer
    assert "RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters" in installer


def test_install_bat_hides_console():
    """install.bat phải tự chạy lại ở chế độ ẩn: không bật cửa sổ cmd."""
    bat = build_install_bat("Neon Pack", {"Arrow": "Normal.cur", "IBeam": "Text.cur"})
    # prologue relaunch ẩn qua wscript, trước mọi công việc cài đặt
    assert 'if "%~1"=="BCM_HIDDEN" goto :install' in bat
    assert 'Set s = CreateObject("WScript.Shell"^)' in bat
    assert 's.Run "cmd /c ""%~f0"" BCM_HIDDEN", 0, False' in bat
    assert 'cscript //nologo "%VBS%" >nul 2>&1' in bat
    assert bat.index(":install") < bat.index("net session")
    # instance nâng quyền cũng chạy ẩn
    assert "-WindowStyle Hidden" in bat
    assert "-ArgumentList 'BCM_HIDDEN'" in bat
    # các dòng cài đặt cốt lõi vẫn nguyên
    assert 'set "PACK_DIR=%WINDIR%\\Cursors\\Neon Pack"' in bat
    assert 'reg add "HKCU\\Control Panel\\Cursors" /v "Arrow"' in bat


def test_install_bat_relaunch_runs_body_hidden(tmp_path):
    """Chạy thật prologue: instance ẩn phải thực thi được phần thân (dùng body đánh dấu, không đụng registry)."""
    import os
    import subprocess

    full = build_install_bat("Neon Pack", {"Arrow": "Normal.cur"})
    # cắt ở dòng nhãn ":install" (dòng riêng), không phải "goto :install"
    prologue = full.split("\r\n:install\r\n", 1)[0] + "\r\n:install\r\n"
    marker = tmp_path / "relaunch-marker.txt"
    body = f'echo done > "{marker}"\r\n'
    bat_file = tmp_path / "test_install.bat"
    # build_install_bat đã có sẵn \r\n -> ghi nhị phân, không để text mode dịch lại
    bat_file.write_bytes((prologue + body).encode("utf-8"))
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    result = subprocess.run(
        [os.environ.get("COMSPEC", "cmd.exe"), "/c", str(bat_file)],
        capture_output=True,
        text=True,
        timeout=30,
        creationflags=flags,
    )
    assert result.returncode == 0, result.stderr
    # relaunch bất đồng bộ (s.Run 0, False) -> instance ẩn cần chút thời gian để spawn
    import time

    deadline = time.time() + 5
    while not marker.exists() and time.time() < deadline:
        time.sleep(0.1)
    assert marker.exists(), "instance ẩn (wscript) không chạy được phần thân"


def test_install_bat_activates_only_assigned_roles_and_uses_safe_folder():
    bat = build_install_bat('Neon & "Pack"', {"Arrow": "Normal.cur", "IBeam": "Text.cur"})
    assert 'set "PACK_DIR=%WINDIR%\\Cursors\\Neon & Pack"' in bat
    assert 'reg add "HKCU\\Control Panel\\Cursors" /v "Arrow"' in bat
    assert 'reg add "HKCU\\Control Panel\\Cursors" /v "IBeam"' in bat
    assert '/v "Wait"' not in bat
    assert 'reg add "HKCU\\Control Panel\\Cursors" /ve' in bat
