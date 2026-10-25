#!/usr/bin/env python3
# Wallpaper GIF Converter
# Made by snuver
# Turns Wallpaper Engine stuff into GIF because apparently nobody else wanted to make this SIGHHHHH 😭.

import argparse
import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
import uuid
from pathlib import Path

APP_NAME = "Wallpaper GIF Converter v1.5"
APP_VERSION = "1.5"
CAPTURE_BACKEND = "DESKTOP REGION"
WINDOW_NAME = "WE_TO_GIF_CAPTURE"
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
VIDEO_EXTS = {".mp4", ".webm", ".mkv", ".avi", ".mov", ".wmv", ".m4v"}


def log(msg):
    print(f"[{APP_NAME}] {msg}", flush=True)


def die(msg, code=1):
    print(f"\nERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def run(cmd, check=True, cwd=None, capture=False):
    if capture:
        return subprocess.run(cmd, check=check, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return subprocess.run(cmd, check=check, cwd=cwd)


def find_project(root):
    candidates = list(root.rglob("project.json"))
    if not candidates:
        die("I could not find project.json. This does not look like a Wallpaper Engine wallpaper.")
    return min(candidates, key=lambda p: len(p.parts)).parent


def get_input(input_path, temp_root):
    if input_path.is_dir():
        return find_project(input_path)
    if input_path.suffix.lower() == ".zip":
        extract_dir = temp_root / "wallpaper"
        extract_dir.mkdir(parents=True, exist_ok=True)
        log("Unzipping the wallpaper...")
        with zipfile.ZipFile(input_path, "r") as zf:
            zf.extractall(extract_dir)
        return find_project(extract_dir)
    if input_path.name.lower() == "project.json":
        return input_path.parent
    if input_path.suffix.lower() in VIDEO_EXTS:
        return input_path
    die("Give me a Wallpaper Engine ZIP/folder/project.json or a normal video file.")


def load_project(project_root):
    project_path = project_root / "project.json"
    with project_path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def get_scene_size(project_root):
    # this is kinda hacky but the size is usually readable inside scene.pkg
    pkg = project_root / "scene.pkg"
    if not pkg.exists():
        return None
    try:
        data = pkg.read_bytes().decode("latin1", errors="ignore")
        m = re.search(r'"orthogonalprojection"\s*:\s*\{.{0,500}?"height"\s*:\s*(\d+).{0,200}?"width"\s*:\s*(\d+)', data, re.S)
        if m:
            h, w = int(m.group(1)), int(m.group(2))
            if 100 <= w <= 10000 and 100 <= h <= 10000:
                return w, h
        m = re.search(r'"orthogonalprojection"\s*:\s*\{.{0,500}?"width"\s*:\s*(\d+).{0,200}?"height"\s*:\s*(\d+)', data, re.S)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
            if 100 <= w <= 10000 and 100 <= h <= 10000:
                return w, h
    except Exception:
        pass
    return None


def get_wallpaper_file(project_root, project):
    raw = str(project.get("file", ""))
    candidate = project_root / raw
    if candidate.exists():
        return candidate
    if str(project.get("type", "")).lower() == "scene" and (project_root / "scene.pkg").exists():
        return project_root / "project.json"
    return project_root / "project.json"


def get_ffmpeg(app_dir, auto_download=True):
    # check PATH first
    for name in ["ffmpeg.exe", "ffmpeg"]:
        p = shutil.which(name)
        if p:
            return Path(p)
    bundled = app_dir / "tools" / "ffmpeg.exe"
    if bundled.exists():
        return bundled
    if os.name != "nt":
        die("ffmpeg was not found in PATH.")
    if not auto_download:
        die("ffmpeg was not found. Re-run without --no-download, or install ffmpeg.")

    tools = app_dir / "tools"
    tools.mkdir(parents=True, exist_ok=True)
    archive = tools / "ffmpeg.zip"
    log("No ffmpeg found, downloading it...")
    urllib.request.urlretrieve(FFMPEG_URL, archive)
    log("ffmpeg downloaded, unzipping...")
    with zipfile.ZipFile(archive, "r") as zf:
        ffmpeg_member = next((n for n in zf.namelist() if n.lower().endswith("/bin/ffmpeg.exe")), None)
        if not ffmpeg_member:
            die("Downloaded ffmpeg archive did not contain ffmpeg.exe.")
        with zf.open(ffmpeg_member) as src, bundled.open("wb") as dst:
            shutil.copyfileobj(src, dst)
    archive.unlink(missing_ok=True)
    return bundled


def find_we(explicit=None):
    if explicit:
        p = Path(explicit).expanduser()
        if p.is_dir():
            for exe in ("wallpaper64.exe", "wallpaper32.exe"):
                if (p / exe).exists():
                    return p / exe
        if p.exists():
            return p
        die(f"Wallpaper Engine executable not found: {p}")

    if os.name != "nt":
        die("Scene wallpapers require Wallpaper Engine on Windows.")

    # check the normal install folders first
    candidates = []
    pf86 = os.environ.get("ProgramFiles(x86)")
    pf = os.environ.get("ProgramFiles")
    if pf86:
        candidates.append(Path(pf86) / "Steam/steamapps/common/wallpaper_engine/wallpaper64.exe")
    if pf:
        candidates.append(Path(pf) / "Steam/steamapps/common/wallpaper_engine/wallpaper64.exe")

    # then try the registry because steam can be installed basically anywhere
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\WallpaperEngine") as key:
            install, _ = winreg.QueryValueEx(key, "installPath")
            candidates.insert(0, Path(install) / "wallpaper64.exe")
    except Exception:
        pass

    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            steam, _ = winreg.QueryValueEx(key, "SteamPath")
            candidates.append(Path(steam) / "steamapps/common/wallpaper_engine/wallpaper64.exe")
    except Exception:
        pass

    for p in candidates:
        if p.exists():
            return p

    die("I could not find Wallpaper Engine. If it is installed somewhere weird, use --wallpaper-engine with wallpaper64.exe.")


def open_we(we_exe):
    log("Opening Wallpaper Engine...")
    subprocess.Popen([str(we_exe)], cwd=str(we_exe.parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2.0)


def open_wallpaper_window(we_exe, project_json, width, height):
    cmd = [
        str(we_exe), "-control", "openWallpaper",
        "-file", str(project_json),
        "-playInWindow", WINDOW_NAME,
        "-width", str(width), "-height", str(height),
        "-x", "0", "-y", "0",
        "-borderless",
        "-activate"
    ]
    log(f"Opening the wallpaper at {width}x{height}...")
    run(cmd, cwd=str(we_exe.parent))
    time.sleep(3.0)


def close_wallpaper_window(we_exe):
    try:
        run([str(we_exe), "-control", "closeWallpaper", "-location", WINDOW_NAME], check=False, cwd=str(we_exe.parent))
    except Exception:
        pass


def fix_windows_scaling():
    # windows scaling messed up the capture position for me, so fix that here
    if os.name != "nt":
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def get_window_info(timeout=10.0):
    # get the actual part of the window that contains the wallpaper
    if os.name != "nt":
        return None

    user32 = ctypes.windll.user32

    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

    deadline = time.time() + timeout
    hwnd = None
    while time.time() < deadline:
        hwnd = user32.FindWindowW(None, WINDOW_NAME)
        if hwnd:
            break
        time.sleep(0.15)

    if not hwnd:
        return None

    outer = RECT()
    client = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(outer)):
        return None
    if not user32.GetClientRect(hwnd, ctypes.byref(client)):
        return None

    origin = POINT(0, 0)
    if not user32.ClientToScreen(hwnd, ctypes.byref(origin)):
        return None

    outer_w = outer.right - outer.left
    outer_h = outer.bottom - outer.top
    client_w = client.right - client.left
    client_h = client.bottom - client.top

    if client_w <= 0 or client_h <= 0:
        return None

    return {
        "hwnd": int(hwnd),
        "outer_left": int(outer.left),
        "outer_top": int(outer.top),
        "outer_width": int(outer_w),
        "outer_height": int(outer_h),
        "client_left": int(origin.x),
        "client_top": int(origin.y),
        "client_width": int(client_w),
        "client_height": int(client_h),
    }


def keep_window_on_top(metrics):
    # gdigrab records what is actually visible, so keep this window in front
    if os.name != "nt" or not metrics:
        return
    try:
        user32 = ctypes.windll.user32
        hwnd = ctypes.c_void_p(metrics["hwnd"])
        HWND_TOPMOST = ctypes.c_void_p(-1)
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_SHOWWINDOW = 0x0040
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                            SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
        time.sleep(0.25)
    except Exception:
        pass


def default_output_folder():
    # try to use the real Videos folder instead of guessing the path
    if os.name == "nt":
        try:
            class GUID(ctypes.Structure):
                _fields_ = [
                    ("Data1", ctypes.c_uint32),
                    ("Data2", ctypes.c_uint16),
                    ("Data3", ctypes.c_uint16),
                    ("Data4", ctypes.c_ubyte * 8),
                ]

            raw = uuid.UUID("18989B1D-99B5-455B-841C-AB7C74E4DDFC").bytes_le
            folder_id = GUID.from_buffer_copy(raw)
            path_ptr = ctypes.c_wchar_p()
            shell32 = ctypes.windll.shell32
            ole32 = ctypes.windll.ole32
            shell32.SHGetKnownFolderPath.argtypes = [
                ctypes.POINTER(GUID), ctypes.c_uint32, ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_wchar_p)
            ]
            shell32.SHGetKnownFolderPath.restype = ctypes.c_long
            ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
            ole32.CoTaskMemFree.restype = None
            result = shell32.SHGetKnownFolderPath(
                ctypes.byref(folder_id), 0, None, ctypes.byref(path_ptr)
            )
            if result == 0 and path_ptr.value:
                try:
                    return Path(path_ptr.value) / "Wallpaper GIF Converter"
                finally:
                    ole32.CoTaskMemFree(ctypes.cast(path_ptr, ctypes.c_void_p))
        except Exception:
            pass
        return Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Videos" / "Wallpaper GIF Converter"
    return Path.home() / "Videos" / "Wallpaper GIF Converter"


def recommended_settings(detected_size):
    # these looked decent without making ridiculously huge gifs
    duration = 10
    fps = 12
    if detected_size:
        dw, dh = detected_size
        width = min(dw, 1280)
        if width % 2:
            width -= 1
        height = max(2, round(width * dh / dw))
        if height % 2:
            height += 1
    else:
        width, height = 1280, 720
    return duration, fps, width, height


def get_screen_size():
    if os.name != "nt":
        return None
    try:
        user32 = ctypes.windll.user32
        return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))
    except Exception:
        return None


def fit_render_to_screen(width, height):
    screen = get_screen_size()
    if not screen:
        return width, height
    screen_w, screen_h = screen
    scale = min(1.0, screen_w / width, screen_h / height)
    if scale >= 1.0:
        return width, height
    width = max(2, int(width * scale))
    height = max(2, int(height * scale))
    width -= width % 2
    height -= height % 2
    return width, height


def find_render_area(metrics, wanted_w, wanted_h):
    left = metrics["client_left"]
    top = metrics["client_top"]

    if os.name == "nt":
        try:
            user32 = ctypes.windll.user32

            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                            ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

            candidates = []
            CALLBACK = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

            def check_child(hwnd, _):
                rect = RECT()
                if user32.IsWindowVisible(hwnd) and user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    w = int(rect.right - rect.left)
                    h = int(rect.bottom - rect.top)
                    if w > 100 and h > 100:
                        score = abs(w - wanted_w) + abs(h - wanted_h)
                        candidates.append((score, int(rect.left), int(rect.top), w, h))
                return True

            callback = CALLBACK(check_child)
            user32.EnumChildWindows(ctypes.c_void_p(metrics["hwnd"]), callback, 0)
            if candidates:
                best = min(candidates, key=lambda x: x[0])
                if best[0] <= 16:
                    _, left, top, _, _ = best
        except Exception:
            pass

    screen = get_screen_size()
    if screen:
        screen_w, screen_h = screen
        left = max(0, min(left, max(0, screen_w - wanted_w)))
        top = max(0, min(top, max(0, screen_h - wanted_h)))

    return left, top, wanted_w, wanted_h


def record_scene(ffmpeg, duration, fps, temp_video, render_w, render_h):
    metrics = get_window_info()
    if not metrics:
        die("I opened the wallpaper but could not find its capture window on screen.")

    keep_window_on_top(metrics)
    metrics = get_window_info(timeout=2.0) or metrics

    outer_w = metrics["outer_width"]
    outer_h = metrics["outer_height"]
    left, top, width, height = find_render_area(metrics, render_w, render_h)

    log(f"Window size: {outer_w}x{outer_h}")
    if outer_w != render_w or outer_h != render_h:
        log(f"Windows wrapper is bigger than the wallpaper. Ignoring it and grabbing {render_w}x{render_h} instead.")
    log(f"Actual wallpaper area: {width}x{height} at ({left},{top})")
    log("Capture mode: DESKTOP REGION")
    log("Recording the visible wallpaper because direct capture kept giving me black video.")

    safe_w = width - (width % 2)
    safe_h = height - (height % 2)

    cmd = [
        str(ffmpeg), "-hide_banner", "-loglevel", "warning", "-y",
        "-f", "gdigrab",
        "-draw_mouse", "0",
        "-framerate", str(fps),
        "-offset_x", str(left),
        "-offset_y", str(top),
        "-video_size", f"{safe_w}x{safe_h}",
        "-i", "desktop",
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "12",
        "-pix_fmt", "yuv420p",
        str(temp_video)
    ]
    log(f"Recording {duration:g} seconds at {fps} FPS...")
    log(f"Recording area: ({left},{top}) {safe_w}x{safe_h}")
    run(cmd)


def probe_video_width(ffmpeg, source_video):
    ffprobe = ffmpeg.with_name("ffprobe.exe" if ffmpeg.suffix.lower() == ".exe" else "ffprobe")
    if not ffprobe.exists():
        return None
    try:
        result = run([
            str(ffprobe), "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width", "-of", "csv=p=0", str(source_video)
        ], capture=True)
        return int(result.stdout.strip())
    except Exception:
        return None


def encode_gif(ffmpeg, source_video, output, fps, width, colors, bayer_scale, loop):
    scale = f"scale={width}:-2:flags=lanczos" if width > 0 else "scale=iw:ih:flags=lanczos"
    vf = (
        f"fps={fps},{scale},split[s0][s1];"
        f"[s0]palettegen=max_colors={colors}:stats_mode=diff[p];"
        f"[s1][p]paletteuse=dither=bayer:bayer_scale={bayer_scale}:diff_mode=rectangle"
    )
    cmd = [
        str(ffmpeg), "-hide_banner", "-loglevel", "warning", "-y",
        "-i", str(source_video),
        "-filter_complex", vf,
        "-gifflags", "+offsetting+transdiff",
        "-loop", str(loop),
        str(output)
    ]
    run(cmd)


def make_gif(ffmpeg, source_video, output, fps, gif_width, loop, target_mb=5.0):
    target_bytes = int(target_mb * 1_000_000)
    source_width = probe_video_width(ffmpeg, source_video)
    requested_width = gif_width if gif_width > 0 else (source_width or 1280)
    requested_width = max(2, requested_width - (requested_width % 2))

    if target_mb <= 0:
        log("Making the gif now... this part is kinda slow lol.")
        encode_gif(ffmpeg, source_video, output, fps, requested_width, 256, 3, loop)
        return

    log(f"Trying to keep this under {target_mb:g} MB without making it look crunchy...")
    log(f"Keeping {fps} FPS. Size/colors get adjusted only if they have to.")

    with tempfile.TemporaryDirectory(prefix="we2gif_opt_") as td:
        td = Path(td)
        tries = []
        width = requested_width
        colors = 256
        bayer = 3

        for attempt in range(1, 8):
            candidate = td / f"try_{attempt}.gif"
            log(f"Quality try {attempt}: {width}px wide, {colors} colors")
            encode_gif(ffmpeg, source_video, candidate, fps, width, colors, bayer, loop)
            size = candidate.stat().st_size
            size_mb = size / 1_000_000
            tries.append((size, width, colors, candidate))
            log(f"That one is {size_mb:.2f} MB")

            if size <= target_bytes:
                shutil.copy2(candidate, output)
                log(f"Got it under target: {size_mb:.2f} MB at {width}px / {colors} colors / {fps} FPS")
                return

            ratio = target_bytes / size
            if attempt == 1 and colors > 160:
                colors = 160
                bayer = 3
                continue
            if attempt == 2 and colors > 128:
                colors = 128

            shrink = max(0.68, min(0.92, (ratio ** 0.5) * 1.08))
            next_width = int(width * shrink)
            next_width -= next_width % 2

            if next_width >= width:
                next_width = width - 64
            width = max(360, next_width)

            if width <= requested_width * 0.75:
                colors = min(colors, 96)
                bayer = 3
            if width <= requested_width * 0.55:
                colors = min(colors, 64)
                bayer = 4
            if width <= 480:
                colors = min(colors, 48)
                bayer = 4
            if width <= 400:
                colors = min(colors, 32)
                bayer = 5

        under = [x for x in tries if x[0] <= target_bytes]
        if under:
            best = max(under, key=lambda x: (x[1], x[2]))
        else:
            best = min(tries, key=lambda x: x[0])
        shutil.copy2(best[3], output)
        final_mb = best[0] / 1_000_000
        if final_mb > target_mb:
            log(f"Could not hit {target_mb:g} MB without absolutely destroying it. Smallest decent try: {final_mb:.2f} MB")
        else:
            log(f"Final GIF: {final_mb:.2f} MB")


def video_to_gif(ffmpeg, video, output, duration, fps, gif_width, loop, target_mb):
    with tempfile.TemporaryDirectory(prefix="we2gif_video_") as td:
        clipped = Path(td) / "clip.mp4"
        cmd = [
            str(ffmpeg), "-hide_banner", "-loglevel", "warning", "-y",
            "-i", str(video), "-t", f"{duration:.3f}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-an", str(clipped)
        ]
        log(f"Using the first {duration:g} seconds of the video...")
        run(cmd)
        make_gif(ffmpeg, clipped, output, fps, gif_width, loop, target_mb)


def main():
    fix_windows_scaling()
    ap = argparse.ArgumentParser(description="turn Wallpaper Engine wallpapers into gifs")
    ap.add_argument("input", help="Wallpaper Engine .zip/folder/project.json, or video file")
    ap.add_argument("-o", "--output", help="Output GIF path")
    ap.add_argument("-d", "--duration", type=float, default=10.0, help="Capture/trim length in seconds (default: 10)")
    ap.add_argument("--fps", type=int, default=12, help="GIF/capture FPS (default/recommended: 12)")
    ap.add_argument("--render-width", type=int, default=0, help="Scene render width (0 = auto)")
    ap.add_argument("--render-height", type=int, default=0, help="Scene render height (0 = auto)")
    ap.add_argument("--gif-width", type=int, default=1280, help="GIF width, 0 = full render width (default: 1280)")
    ap.add_argument("--loop", type=int, default=0, help="GIF loop count; 0 = infinite")
    ap.add_argument("--target-mb", type=float, default=5.0, help="Try to keep the GIF under this many MB; 0 disables size targeting (default: 5)")
    ap.add_argument("--wallpaper-engine", help="Path to wallpaper64.exe or Wallpaper Engine folder")
    ap.add_argument("--no-download", action="store_true", help="Do not auto-download ffmpeg on Windows")
    ap.add_argument("--inspect", action="store_true", help="Inspect/classify only; do not capture/convert")
    args = ap.parse_args()

    print("=" * 62)
    print(" Wallpaper GIF Converter v1.5")
    print(" Made by snuver")
    print(" Turns Wallpaper Engine wallpapers into GIFs. Simple as that.")
    print(" Capture mode: DESKTOP REGION")
    print(" Saves to: Videos\\Wallpaper GIF Converter")
    print("=" * 62, flush=True)

    if args.duration <= 0 or args.duration > 600:
        die("Duration must be between 0 and 600 seconds.")
    if args.fps < 1 or args.fps > 60:
        die("FPS must be between 1 and 60.")
    if args.target_mb < 0:
        die("Target MB cannot be negative.")

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        die(f"Input does not exist: {input_path}")

    app_dir = Path(__file__).resolve().parent
    if args.output:
        out = Path(args.output).expanduser().resolve()
    else:
        output_dir = default_output_folder()
        output_dir.mkdir(parents=True, exist_ok=True)
        out = output_dir / f"{input_path.stem}.gif"
    out.parent.mkdir(parents=True, exist_ok=True)
    log(f"Your GIF is going here: {out}")

    with tempfile.TemporaryDirectory(prefix="we2gif_") as td:
        temp_root = Path(td)
        prepared = get_input(input_path, temp_root)

        if isinstance(prepared, Path) and prepared.is_file() and prepared.suffix.lower() in VIDEO_EXTS:
            mode = "video"
            video_file = prepared
            project = None
            project_root = None
        else:
            project_root = prepared
            project = load_project(project_root)
            mode = str(project.get("type", "")).lower()
            video_file = get_wallpaper_file(project_root, project)

        log(f"Wallpaper type: {mode or 'unknown'}")
        if project:
            log(f"Wallpaper: {project.get('title', '(untitled)')}")

        detected_size = get_scene_size(project_root) if project_root and mode == "scene" else None
        if detected_size:
            log(f"Original size: {detected_size[0]}x{detected_size[1]}")

        rec_duration, rec_fps, rec_width, rec_height = recommended_settings(detected_size)
        if mode == "scene":
            log(f"What I recommend: {rec_duration}s, {rec_fps} FPS, {rec_width}x{rec_height} ({rec_duration * rec_fps} frames)")

        if args.inspect:
            print(json.dumps({
                "type": mode,
                "title": project.get("title") if project else None,
                "project_root": str(project_root) if project_root else None,
                "resolved_file": str(video_file),
                "detected_scene_size": detected_size,
            }, indent=2))
            return

        ffmpeg = get_ffmpeg(app_dir, auto_download=not args.no_download)
        log(f"FFmpeg: {ffmpeg}")

        if mode == "video" or (video_file.is_file() and video_file.suffix.lower() in VIDEO_EXTS):
            video_to_gif(ffmpeg, video_file, out, args.duration, args.fps, args.gif_width, args.loop, args.target_mb)

        elif mode == "scene":
            if os.name != "nt":
                die("Scene conversion must be run on Windows because Wallpaper Engine is the renderer.")
            we_exe = find_we(args.wallpaper_engine)
            open_we(we_exe)
            dw, dh = detected_size if detected_size else (1920, 1080)
            if args.render_width and args.render_height:
                rw, rh = args.render_width, args.render_height
            elif args.render_width:
                rw = args.render_width
                rh = max(2, round(rw * dh / dw))
            elif args.render_height:
                rh = args.render_height
                rw = max(2, round(rh * dw / dh))
            elif args.gif_width > 0:
                rw = min(args.gif_width, dw)
                rh = max(2, round(rw * dh / dw))
            else:
                rw, rh = dw, dh
            if rw % 2:
                rw -= 1
            if rh % 2:
                rh += 1
            fitted_rw, fitted_rh = fit_render_to_screen(rw, rh)
            if (fitted_rw, fitted_rh) != (rw, rh):
                log(f"{rw}x{rh} is bigger than the screen, so I'm rendering at {fitted_rw}x{fitted_rh} instead.")
                rw, rh = fitted_rw, fitted_rh
            log(f"Rendering at: {rw}x{rh}")
            temp_video = temp_root / "scene_capture.mp4"
            try:
                close_wallpaper_window(we_exe)
                time.sleep(0.3)
                open_wallpaper_window(we_exe, project_root / "project.json", rw, rh)
                record_scene(ffmpeg, args.duration, args.fps, temp_video, rw, rh)
            finally:
                close_wallpaper_window(we_exe)
            make_gif(ffmpeg, temp_video, out, args.fps, args.gif_width, args.loop, args.target_mb)

        elif mode == "web":
            die("Web wallpapers are not supported yet. Scene and video wallpapers are good though.")
        else:
            die(f"Unsupported/unknown wallpaper type: {mode!r}")

    size_mb = out.stat().st_size / 1_000_000
    print(f"\nDONE. Your GIF is here:\n{out}\n\nSize: {size_mb:.2f} MB\nMade by snuver")


if __name__ == "__main__":
    main()
