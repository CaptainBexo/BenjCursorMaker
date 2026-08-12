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
    export_installer_into_folder,
    map_folder_to_roles,
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
    """build_ani -> parse_ani round-trips frames, hotspot and rates."""
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
    """run.bat must relaunch itself hidden and start the app with pythonw (no console)."""
    from pathlib import Path

    run_bat = Path(__file__).resolve().parent.parent / "run.bat"
    assert run_bat.exists()
    content = run_bat.read_text(encoding="utf-8", errors="replace")
    assert 'if "%~1"=="BCM_HIDDEN" goto :run' in content
    assert 'Set s = CreateObject("WScript.Shell"^)' in content
    assert "s.Run \"cmd /c \"\"%~f0\"\" BCM_HIDDEN\", 0, False" in content
    assert "pythonw.exe" in content
    # app runs on the REAL pythonw (GUI subsystem, ws=1 -> window shows, no console) + PYTHONPATH to venv
    assert 's.Run """%PYW%"" main.py", 1, False' in content
    assert 'set "PYTHONPATH=%~dp0.venv\\Lib\\site-packages"' in content
    assert 'findstr /b "home" ".venv\\pyvenv.cfg"' in content
    assert "start \"\"" not in content
    # no longer runs the app with console-bound python.exe
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
    installer = (target / "install.bat").read_text(encoding="utf-8")
    assert "InstallHinfSection DefaultInstall 132" in installer
    assert "Start-Process" in installer
    assert "-Verb RunAs" in installer
    assert 'reg add "HKCU\\Control Panel\\Cursors" /v "Arrow"' in installer
    assert 'reg add "HKCU\\Control Panel\\Cursors" /v "Scheme Source"' in installer
    assert "RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters" in installer
    # lỗi phải hiển thị được (messagebox), không pause trong cửa sổ ẩn
    assert "MessageBox]::Show" in installer


def test_exported_pack_files_have_no_bom_and_clean_endings(tmp_path):
    """install.bat / install.inf không BOM (cmd + setupapi hỏng nếu có BOM), README.txt tiếng Anh + CRLF sạch."""
    target = export_cursorpack_folder(
        tmp_path,
        "Neon",
        {"Arrow": Path("Normal.cur"), "Help": Path("Help.ani")},
        {
            Path("Normal.cur"): b"CUR",
            Path("Help.ani"): b"ANI",
        },
    )
    bat = (target / "install.bat").read_bytes()
    inf = (target / "install.inf").read_bytes()
    readme = (target / "README.txt").read_bytes()
    # không BOM
    assert bat[:3] != b"\xef\xbb\xbf", bat[:8]
    assert inf[:3] != b"\xef\xbb\xbf", inf[:8]
    # CRLF chuẩn, không double-CR
    assert b"\r\n" in bat and b"\r\r\n" not in bat
    assert b"\r\n" in inf and b"\r\r\n" not in inf
    assert b"\r\r\n" not in readme
    # README tiếng Anh
    assert b"Double-click install.bat" in readme
    assert b"Administrator permission" in readme


def test_install_bat_hides_console():
    """install.bat must relaunch itself hidden: no cmd window appears."""
    bat = build_install_bat("Neon Pack", {"Arrow": "Normal.cur", "IBeam": "Text.cur"})
    # hidden wscript relaunch prologue, before any install work
    assert 'if "%~1"=="BCM_HIDDEN" goto :install' in bat
    assert 'Set s = CreateObject("WScript.Shell"^)' in bat
    assert 's.Run "cmd /c ""%~f0"" BCM_HIDDEN", 0, False' in bat
    assert 'cscript //nologo "%VBS%" >nul 2>&1' in bat
    assert bat.index(":install") < bat.index("net session")
    # the elevated instance also runs hidden
    assert "-WindowStyle Hidden" in bat
    assert "-ArgumentList 'BCM_HIDDEN'" in bat
    # core install lines stay intact
    assert 'set "PACK_DIR=%WINDIR%\\Cursors\\Neon Pack"' in bat
    assert 'reg add "HKCU\\Control Panel\\Cursors" /v "Arrow"' in bat


def test_install_bat_relaunch_runs_body_hidden(tmp_path):
    """Run the real prologue: the hidden instance must execute the body (marker body, no registry touch)."""
    import os
    import subprocess

    full = build_install_bat("Neon Pack", {"Arrow": "Normal.cur"})
    # cut at the ":install" label line (own line), not "goto :install"
    prologue = full.split("\r\n:install\r\n", 1)[0] + "\r\n:install\r\n"
    marker = tmp_path / "relaunch-marker.txt"
    body = f'echo done > "{marker}"\r\n'
    bat_file = tmp_path / "test_install.bat"
    # build_install_bat already emits \r\n -> write bytes, avoid text-mode translation
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
    # async relaunch (s.Run 0, False) -> the hidden instance needs a moment to spawn
    import time

    deadline = time.time() + 5
    while not marker.exists() and time.time() < deadline:
        time.sleep(0.1)
    assert marker.exists(), "hidden instance (wscript) did not run the body"


def test_install_bat_activates_only_assigned_roles_and_uses_safe_folder():
    bat = build_install_bat('Neon & "Pack"', {"Arrow": "Normal.cur", "IBeam": "Text.cur"})
    assert 'set "PACK_DIR=%WINDIR%\\Cursors\\Neon & Pack"' in bat
    assert 'reg add "HKCU\\Control Panel\\Cursors" /v "Arrow"' in bat
    assert 'reg add "HKCU\\Control Panel\\Cursors" /v "IBeam"' in bat
    assert '/v "Wait"' not in bat
    assert 'reg add "HKCU\\Control Panel\\Cursors" /ve' in bat


def test_map_folder_to_roles_known_filenames(tmp_path):
    """Folder chứa file tên chuẩn Windows -> map đúng role."""
    (tmp_path / "Normal.cur").write_bytes(b"x")
    (tmp_path / "Help.ani").write_bytes(b"x")
    (tmp_path / "Text.cur").write_bytes(b"x")
    roles = map_folder_to_roles(tmp_path)
    assert roles == {"Arrow": "Normal.cur", "Help": "Help.ani", "IBeam": "Text.cur"}


def test_map_folder_to_roles_fallback_unknown_names(tmp_path):
    """File tên lạ -> gán theo thứ tự role chưa dùng (Arrow, Help, ...)."""
    (tmp_path / "A.cur").write_bytes(b"x")
    (tmp_path / "B.cur").write_bytes(b"x")
    roles = map_folder_to_roles(tmp_path)
    assert roles == {"Arrow": "A.cur", "Help": "B.cur"}


def test_map_folder_to_roles_no_cursors_raises(tmp_path):
    import pytest as _pytest
    with _pytest.raises(ValueError):
        map_folder_to_roles(tmp_path)


def test_export_installer_into_folder_creates_clean_files(tmp_path):
    """Sinh install.bat/inf/README vào folder có sẵn: không BOM, CRLF sạch, map đúng."""
    (tmp_path / "Normal.cur").write_bytes(b"x")
    (tmp_path / "Hand.ani").write_bytes(b"x")
    roles = export_installer_into_folder(tmp_path)
    assert roles == {"Arrow": "Normal.cur", "Hand": "Hand.ani"}
    bat = (tmp_path / "install.bat").read_bytes()
    inf = (tmp_path / "install.inf").read_bytes()
    assert bat[:3] != b"\xef\xbb\xbf"
    assert inf[:3] != b"\xef\xbb\xbf"
    assert b"\r\r\n" not in bat and b"\r\r\n" not in inf
    assert b'reg add "HKCU\Control Panel\Cursors" /v "Hand"' in bat
    assert b"Hand.ani" in inf
    readme = (tmp_path / "README.txt").read_bytes()
    assert b"Double-click install.bat" in readme
