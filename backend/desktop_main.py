"""Desktop entrypoint for the packaged Windows build (PyInstaller).

Starts a bundled portable MongoDB, auto-detects LibreOffice, sets local env,
launches the FastAPI app (which also serves the built React frontend) in a
background thread, then opens a NATIVE desktop window (pywebview / Edge WebView2)
pointing at the local server. NO external browser is opened. NOT used in the
cloud dev environment.
"""
import os
import sys
import time
import socket
import threading
import subprocess
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8001
MONGO_PORT = 27017
LOCK_PORT = 8766  # loopback port used purely as a single-instance guard

_MONGO_PROC = None
_LOCK_SOCK = None  # keep the single-instance socket alive for the whole process


def _port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def acquire_single_instance() -> bool:
    """Return True if we are the only running instance.

    Binds a fixed loopback port WITHOUT address reuse — a second launch cannot
    bind the same port and therefore knows another copy is already running.
    This makes repeated clicks on the icon a no-op instead of spawning several
    copies that fight over the MongoDB / server ports.
    """
    global _LOCK_SOCK
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((HOST, LOCK_PORT))
        s.listen(1)
        _LOCK_SOCK = s
        return True
    except OSError:
        try:
            s.close()
        except Exception:
            pass
        return False


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).parent


def app_root() -> Path:
    """Folder that actually contains the installed app (next to the .exe)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def app_data() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Banetskaya"
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)
    return root


def wait_port(host: str, port: int, timeout: float = 40.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            if s.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.5)
    return False


def start_mongo(base: Path, data_dir: Path, log_dir: Path):
    global _MONGO_PROC
    # A previous copy (or a hard-killed run) may have left MongoDB running.
    # Reuse it instead of starting a second mongod on the same dbpath (which
    # would fail on the lock file).
    if _port_in_use("127.0.0.1", MONGO_PORT):
        print("[info] MongoDB already running on 27017 — reusing it")
        return None
    # mongod may be bundled either inside the onefile temp (base) or next to the exe.
    candidates = [base / "mongodb" / "mongod.exe", app_root() / "mongodb" / "mongod.exe"]
    mongod = next((c for c in candidates if c.exists()), None)
    if not mongod:
        print("[warn] mongod.exe not bundled — expecting an external MongoDB on 27017")
        return None
    logfile = log_dir / "mongod.log"
    print("[info] starting bundled MongoDB ...")
    proc = subprocess.Popen(
        [
            str(mongod),
            "--dbpath", str(data_dir),
            "--port", str(MONGO_PORT),
            "--bind_ip", "127.0.0.1",
            "--logpath", str(logfile),
        ],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    _MONGO_PROC = proc
    if not wait_port("127.0.0.1", MONGO_PORT, 40):
        print("[error] MongoDB did not start in time — see", logfile)
    else:
        print("[info] MongoDB is up")
    return proc


def stop_mongo():
    global _MONGO_PROC
    if _MONGO_PROC is not None:
        try:
            _MONGO_PROC.terminate()
            try:
                _MONGO_PROC.wait(timeout=8)
            except Exception:
                _MONGO_PROC.kill()
        except Exception:
            pass
        _MONGO_PROC = None


def detect_soffice() -> str:
    # Prefer the LibreOffice tree bundled next to the app.
    bundled = app_root() / "libreoffice" / "program" / "soffice.exe"
    if bundled.exists():
        return str(bundled)
    for c in (
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ):
        if Path(c).exists():
            return c
    return os.environ.get("SOFFICE_BIN", "soffice")


def detect_sumatra() -> str:
    bundled = app_root() / "sumatra" / "SumatraPDF.exe"
    if bundled.exists():
        return str(bundled)
    return os.environ.get("SUMATRA_BIN", "SumatraPDF.exe")


def _on_window_closed():
    """User closed the native window -> stop everything."""
    stop_mongo()
    os._exit(0)


def main():
    base = base_dir()
    data = app_data()

    # Log startup so any launch failure can be diagnosed later.
    try:
        _log = open(data / "logs" / "startup.log", "a", encoding="utf-8", buffering=1)
        sys.stdout = _log
        sys.stderr = _log
        print("\n===== launch", __import__("datetime").datetime.now().isoformat(), "=====")
    except Exception:
        pass

    # Single-instance guard: if another copy is already running (or starting),
    # do nothing so repeated icon clicks never spawn conflicting copies.
    if not acquire_single_instance():
        print("[info] another instance is already running — exiting this one")
        return

    os.environ.setdefault("MONGO_URL", f"mongodb://127.0.0.1:{MONGO_PORT}")
    os.environ.setdefault("DB_NAME", "banetskaya_db")
    os.environ.setdefault("CORS_ORIGINS", "*")
    os.environ["SOFFICE_BIN"] = detect_soffice()
    os.environ["SUMATRA_BIN"] = detect_sumatra()

    try:
        _run()
    except Exception as e:  # never die silently — record why
        import traceback
        print("[fatal] startup failed:", e)
        traceback.print_exc()
        stop_mongo()
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                f"Не удалось запустить приложение:\n{e}\n\nПодробности: %LOCALAPPDATA%\\Banetskaya\\logs\\startup.log",
                "Banetskaya.by", 0x10,
            )
        except Exception:
            pass


def _run():
    base = base_dir()
    data = app_data()

    start_mongo(base, data / "data", data / "logs")

    import uvicorn
    import server  # reads env configured above at import time

    # Let the in-app updater stop MongoDB and quit cleanly before the installer runs.
    server.set_shutdown_hook(lambda: (stop_mongo()))

    # Only start our own server if the port is free (it should be — we are the
    # single instance). Otherwise reuse whatever is already serving.
    if not _port_in_use(HOST, PORT):
        def run_server():
            uvicorn.run(server.app, host=HOST, port=PORT, log_level="warning")

        threading.Thread(target=run_server, daemon=True).start()

    if not wait_port(HOST, PORT, 60):
        print("[error] backend did not start in time")
        stop_mongo()
        return

    # Keep the local server alive only while the app window is open: the UI pings
    # /api/_ping; when pings stop (window closed) the watchdog exits the process.
    try:
        server.start_idle_watchdog(30)
    except Exception as e:
        print("[warn] watchdog not started:", e)

    # App window via Microsoft Edge / Chrome in "--app" mode: a clean separate
    # window (no tabs, no address bar) that looks like a native program. This is
    # far more reliable than bundling pywebview/pythonnet/WebView2.
    _open_ui()


def _find_chromium() -> str:
    import shutil
    cands = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    ]
    for c in cands:
        if c and Path(c).exists():
            return c
    return shutil.which("msedge") or shutil.which("chrome") or ""


def _open_ui():
    url = f"http://{HOST}:{PORT}"
    browser = _find_chromium()
    profile = str(app_data() / "browser")
    if browser:
        print("[info] opening app window via", browser)
        # Fire-and-forget: Edge/Chrome may fork and the launcher process exits
        # immediately, so we do NOT wait on it. The idle watchdog handles exit
        # when the window is closed (pings stop).
        try:
            subprocess.Popen([
                browser,
                f"--app={url}",
                f"--user-data-dir={profile}",
                "--no-first-run",
                "--no-default-browser-check",
                "--window-size=1360,900",
            ])
        except Exception as e:
            print("[warn] failed to launch browser window:", e)
    else:
        print("[warn] no Edge/Chrome found — opening default browser")
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                "Приложение открыто в браузере.\n\n"
                f"Адрес приложения: {url}\n\n"
                "Для окна как у программы установите Microsoft Edge и запустите снова.",
                "Banetskaya.by", 0x40,
            )
        except Exception:
            pass

    # Keep the process (and the local server) alive. The watchdog will os._exit
    # once the window is closed and keep-alive pings stop.
    try:
        while True:
            time.sleep(1)
    finally:
        stop_mongo()


if __name__ == "__main__":
    main()
