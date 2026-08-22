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

_MONGO_PROC = None


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

    os.environ.setdefault("MONGO_URL", f"mongodb://127.0.0.1:{MONGO_PORT}")
    os.environ.setdefault("DB_NAME", "banetskaya_db")
    os.environ.setdefault("CORS_ORIGINS", "*")
    os.environ["SOFFICE_BIN"] = detect_soffice()
    os.environ["SUMATRA_BIN"] = detect_sumatra()

    start_mongo(base, data / "data", data / "logs")

    import uvicorn
    import server  # reads env configured above at import time

    # Let the in-app updater stop MongoDB and quit cleanly before the installer runs.
    server.set_shutdown_hook(lambda: (stop_mongo()))

    def run_server():
        uvicorn.run(server.app, host=HOST, port=PORT, log_level="warning")

    threading.Thread(target=run_server, daemon=True).start()

    if not wait_port(HOST, PORT, 60):
        print("[error] backend did not start in time")
        stop_mongo()
        return

    # Native desktop window (Edge WebView2). No browser, no console tab.
    import webview
    window = webview.create_window(
        "Banetskaya.by",
        f"http://{HOST}:{PORT}",
        width=1360,
        height=900,
        min_size=(1024, 680),
        confirm_close=False,
    )
    window.events.closed += _on_window_closed
    try:
        webview.start()  # blocks until the window is closed
    finally:
        stop_mongo()


if __name__ == "__main__":
    main()
