"""Two languages: Vietnamese (default) and English — never mixed."""

LANG = "vi"

TRANSLATIONS: dict[str, dict[str, str]] = {
    # --- Toolbar ---
    "btn.import": {"vi": "MỞ ẢNH", "en": "IMPORT"},
    "btn.apply_crop": {"vi": "CẮT VÙNG", "en": "APPLY CROP"},
    "btn.export_cur": {"vi": "XUẤT .CUR", "en": "EXPORT .CUR"},
    "btn.export_ani": {"vi": "XUẤT .ANI", "en": "EXPORT .ANI"},
    "btn.cursorpack": {"vi": "GÓI CURSOR", "en": "CURSORPACK"},
    "btn.play": {"vi": "PHÁT", "en": "PLAY"},
    "btn.pause": {"vi": "TẠM DỪNG", "en": "PAUSE"},
    # --- Editor tooltips ---
    "tip.import": {
        "vi": "Mở PNG, GIF, JPG hoặc BMP. GIF sẽ nạp đủ các frame.",
        "en": "Open PNG, GIF, JPG or BMP. GIF loads all frames.",
    },
    "tip.apply_crop": {
        "vi": "Cắt vùng đang khoanh và áp dụng cùng vùng đó cho mọi frame.",
        "en": "Crop the selected region and apply it to every frame.",
    },
    "tip.export_cur": {
        "vi": "Xuất frame đang xem thành con trỏ tĩnh .cur, kèm hotspot.",
        "en": "Export the current frame as a static .cur cursor, with hotspot.",
    },
    "tip.export_ani": {
        "vi": "Xuất toàn bộ frame thành con trỏ động .ani, giữ tốc độ và hotspot.",
        "en": "Export all frames as an animated .ani cursor, keeping timing and hotspot.",
    },
    "tip.cursorpack": {
        "vi": "Gán cursor (file hoặc gán thẳng vùng crop + hotspot đang chỉnh) vào trạng thái Windows và tạo thư mục pack có install.bat tự cài.",
        "en": "Assign cursors (files or the current crop + hotspot directly) to Windows states and create a pack folder with a self-installing install.bat.",
    },
    "tip.play": {"vi": "Phát hoặc tạm dừng xem trước GIF.", "en": "Play or pause the GIF preview."},
    "tip.frame_slider": {
        "vi": "Kéo để xem và kiểm tra từng frame GIF.",
        "en": "Drag to view and check each GIF frame.",
    },
    "tip.grid_combo": {
        "vi": "Hít mép vùng crop theo lưới 16, 32 hoặc 48 px; OFF để chọn tự do.",
        "en": "Snap the crop region to a 16, 32 or 48 px grid; OFF for free selection.",
    },
    "tip.zoom_in": {
        "vi": "Phóng to vùng xem để chọn pixel chính xác.",
        "en": "Zoom in for precise pixel selection.",
    },
    "tip.zoom_out": {"vi": "Thu nhỏ vùng xem.", "en": "Zoom out the view."},
    "tip.lang": {
        "vi": "Đang hiển thị tiếng Việt — bấm để chuyển sang tiếng Anh.",
        "en": "Currently showing English — click to switch to Vietnamese.",
    },
    "btn.lang": {"vi": "VN", "en": "EN"},
    # --- Groups / canvas ---
    "title.source": {"vi": "NGUỒN / CÁC FRAME GIF", "en": "SOURCE / GIF FRAMES"},
    "title.grid_snap": {"vi": "LƯỚI HÍT / CHỌN VÙNG", "en": "GRID SNAP / SELECTION"},
    "title.hotspot": {"vi": "HOTSPOT // BẤM MỘT PIXEL", "en": "HOTSPOT // CLICK ONE PIXEL"},
    "canvas.empty_crop": {"vi": "IMPORT ẢNH / GIF", "en": "IMPORT IMAGE / GIF"},
    "canvas.empty_hotspot": {"vi": "CROP ĐỂ XEM TRƯỚC", "en": "CROP TO PREVIEW"},
    "hint.no_image": {
        "vi": "IMPORT ẢNH / GIF TRƯỚC — CROP RỒI CHỌN PIXEL LÀM HOTSPOT",
        "en": "IMPORT AN IMAGE / GIF FIRST — CROP, THEN PICK A PIXEL AS HOTSPOT",
    },
    "hotspot.hover": {
        "vi": "X: {x}  Y: {y}   // BẤM ĐỂ ĐẶT HOTSPOT",
        "en": "X: {x}  Y: {y}   // CLICK TO SET HOTSPOT",
    },
    # --- Status bar ---
    "status.ready": {
        "vi": "READY // Import PNG, GIF, JPG hoặc BMP",
        "en": "READY // Import PNG, GIF, JPG or BMP",
    },
    "status.loaded": {"vi": "ĐÃ NẠP // {name} // {n} frame(s)", "en": "LOADED // {name} // {n} frame(s)"},
    "status.cropped": {"vi": "ĐÃ CẮT // {w} × {h} px", "en": "CROPPED // {w} × {h} px"},
    "status.hotspot": {
        "vi": "HOTSPOT ({x}, {y}) ĐÃ ÁP DỤNG CHO {n} FRAME",
        "en": "HOTSPOT ({x}, {y}) APPLIED TO ALL {n} FRAME(S)",
    },
    "status.exported": {"vi": "ĐÃ XUẤT // {path}", "en": "EXPORTED // {path}"},
    "status.packed": {"vi": "ĐÃ TẠO PACK // {path}", "en": "PACKED // {path}"},
    "status.applied": {
        "vi": "APPLIED{detail} // {n} role(s) đã lưu — chỉnh ảnh rồi mở lại CURSORPACK để gán tiếp",
        "en": "APPLIED{detail} // {n} role(s) saved — edit the image, then reopen CURSORPACK to assign more",
    },
    # --- Errors / system dialogs ---
    "error.open": {"vi": "Không thể mở ảnh", "en": "Cannot open image"},
    "error.crop": {"vi": "Crop thất bại", "en": "Crop failed"},
    "error.export_cur": {"vi": "Export CUR thất bại", "en": "Export CUR failed"},
    "error.export_ani": {"vi": "Export ANI thất bại", "en": "Export ANI failed"},
    "error.pack": {"vi": "Tạo cursorpack thất bại", "en": "Failed to create cursorpack"},
    "error.no_image": {"vi": "Hãy import ảnh trước.", "en": "Import an image first."},
    "dialog.open_image": {"vi": "Import ảnh", "en": "Import image"},
    "dialog.pick_pack_dir": {
        "vi": "Chọn nơi tạo thư mục cursorpack",
        "en": "Choose where to create the cursorpack folder",
    },
    "dialog.pack_done": {"vi": "Hoàn tất", "en": "Done"},
    "dialog.pack_done_body": {
        "vi": "Đã tạo thư mục:\n{folder}\n\nVào thư mục đó rồi double-click install.bat. Windows sẽ hỏi quyền Administrator, tự cài và kích hoạt cursor scheme.",
        "en": "Created folder:\n{folder}\n\nGo into the folder and double-click install.bat. Windows will ask for Administrator rights, then install and activate the cursor scheme.",
    },
    # --- CursorPackDialog ---
    "pack.title": {"vi": "TRÌNH TẠO CURSORPACK", "en": "CURSORPACK BUILDER"},
    "pack.scheme_label": {"vi": "Tên scheme:", "en": "Scheme name:"},
    "pack.tip.scheme": {
        "vi": "Tên hiển thị của bộ con trỏ trong Windows.",
        "en": "Display name of the cursor set in Windows.",
    },
    "pack.tip.list": {
        "vi": "Chọn một trạng thái Windows, rồi bấm GÁN để chọn file .cur/.ani hoặc gán thẳng cursor đang chỉnh.",
        "en": "Select a Windows state, then click ASSIGN to pick a .cur/.ani file or assign the current editor cursor directly.",
    },
    "pack.unassigned": {"vi": "— chưa gán —", "en": "— not assigned —"},
    "pack.from_editor": {"vi": " [TỪ EDITOR]", "en": " [FROM EDITOR]"},
    "pack.assign_file": {"vi": "GÁN .CUR / .ANI", "en": "ASSIGN .CUR / .ANI"},
    "pack.clear": {"vi": "BỎ GÁN", "en": "CLEAR"},
    "pack.assign_current": {"vi": "GÁN CURSOR HIỆN TẠI", "en": "ASSIGN CURRENT CURSOR"},
    "pack.assign_all": {"vi": "GÁN CHO TẤT CẢ", "en": "ASSIGN TO ALL"},
    "pack.apply": {"vi": "ÁP DỤNG", "en": "Apply"},
    "pack.save": {"vi": "LƯU", "en": "Save"},
    "pack.cancel": {"vi": "HỦY", "en": "Cancel"},
    "pack.tip.assign_file": {
        "vi": "Gán file .cur hoặc .ani cho trạng thái đang chọn.",
        "en": "Assign a .cur or .ani file to the selected state.",
    },
    "pack.tip.clear": {
        "vi": "Xóa file đã gán khỏi trạng thái đang chọn.",
        "en": "Remove the assignment from the selected state.",
    },
    "pack.tip.assign_current": {
        "vi": "Gán thẳng vùng crop + hotspot đang chỉnh vào trạng thái đang chọn — không cần xuất .cur/.ani.",
        "en": "Assign the current crop + hotspot directly to the selected state — no .cur/.ani export needed.",
    },
    "pack.tip.assign_all": {
        "vi": "Gán thẳng cursor đang chỉnh cho toàn bộ trạng thái trong danh sách.",
        "en": "Assign the current editor cursor to every state in the list.",
    },
    "pack.tip.apply": {
        "vi": "Gán thẳng cursor đang chỉnh vào trạng thái đang chọn và lưu tạm, đóng hộp thoại — chỉnh ảnh rồi mở lại CURSORPACK để gán tiếp.",
        "en": "Assign the current editor cursor to the selected state and save temporarily, close the dialog — edit the image, then reopen CURSORPACK to assign more.",
    },
    "pack.tip.save": {
        "vi": "Tạo thư mục cursorpack (có install.bat) để tự cài và kích hoạt trên Windows.",
        "en": "Create the cursorpack folder (with install.bat) to install and activate on Windows.",
    },
    "pack.tip.cancel": {"vi": "Đóng mà không tạo cursorpack.", "en": "Close without creating a cursorpack."},
    "pack.warn.no_image": {"vi": "Chưa có ảnh", "en": "No image"},
    "pack.warn.no_image_body": {
        "vi": "Hãy import ảnh/GIF, chọn vùng crop và hotspot trước.",
        "en": "Import an image/GIF, select a crop region and hotspot first.",
    },
    "pack.warn.no_role": {"vi": "Chưa chọn trạng thái", "en": "No state selected"},
    "pack.warn.no_role_body": {
        "vi": "Chọn một trạng thái trong danh sách rồi bấm Apply — cursor đang chỉnh sẽ được gán thẳng và lưu tạm.",
        "en": "Select a state in the list and click Apply — the current cursor will be assigned directly and saved temporarily.",
    },
    "pack.warn.missing": {"vi": "Thiếu dữ liệu", "en": "Missing data"},
    "pack.warn.missing_body": {
        "vi": "Nhập tên pack và gán ít nhất một cursor (chọn trạng thái khi có ảnh đang mở, hoặc GÁN .CUR / .ANI).",
        "en": "Enter a pack name and assign at least one cursor (select a state while an image is open, or use ASSIGN .CUR / .ANI).",
    },
    "pack.warn.no_selection": {"vi": "Chưa chọn trạng thái", "en": "No state selected"},
    "pack.warn.no_selection_body": {
        "vi": "Chọn một trạng thái trong danh sách trước.",
        "en": "Select a state in the list first.",
    },
    "pack.choose_cursor": {"vi": "Chọn cursor", "en": "Choose cursor"},
    "btn.installer": {"vi": "INSTALL.BAT", "en": "INSTALL.BAT"},
    "tip.installer": {
        "vi": "Tạo install.bat + install.inf cho folder đã có sẵn file .cur/.ani — không cần tạo lại cursor.",
        "en": "Generate install.bat + install.inf for a folder that already contains .cur/.ani files — no need to recreate cursors.",
    },
    "pack.choose_folder": {
        "vi": "Chọn folder chứa file .cur/.ani",
        "en": "Choose a folder containing .cur/.ani files",
    },
    "pack.scale_label": {"vi": "CỠ CON TRỎ", "en": "POINTER SIZE"},
    "pack.tip.scale": {
        "vi": "Cỡ con trỏ khi cài (100% = mặc định 32px, 200% = 64px…). Không làm méo hình — chỉ đổi kích thước hiển thị trong Windows.",
        "en": "Pointer size applied on install (100% = default 32px, 200% = 64px…). Does not distort the image — only changes the on-screen size in Windows.",
    },
    "warn.no_cursors": {
        "vi": "Folder không chứa file .cur hoặc .ani nào.",
        "en": "The folder contains no .cur or .ani files.",
    },
    "status.installer_created": {
        "vi": "Đã tạo install.bat cho {count} con trỏ trong {folder}",
        "en": "Created install.bat for {count} cursors in {folder}",
    },
    "status.exported_size": {
        "vi": "Đã xuất {w}×{h}: {path}",
        "en": "Exported {w}x{h}: {path}",
    },
}


def set_lang(lang: str) -> None:
    global LANG
    LANG = lang


def get_lang() -> str:
    return LANG


def tr(key: str, **kwargs) -> str:
    text = TRANSLATIONS.get(key, {}).get(LANG, key)
    if kwargs:
        text = text.format(**kwargs)
    return text
