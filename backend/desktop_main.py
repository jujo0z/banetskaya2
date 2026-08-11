"""Desktop entrypoint for the packaged Windows build (PyInstaller).

Starts a bundled portable MongoDB, auto-detects LibreOffice, sets local env,
launches the FastAPI app (which also serves the built React frontend) and opens
the browser. NOT used in the cloud dev environment.
"""
import os
import sys
import time
import socket
import threading
import subprocess
import webbrowser
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8001
MONGO_PORT = 27017


def base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
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
    mongod = base / "mongodb" / "mongod.exe"
    if not mongod.exists():
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
    if not wait_port("127.0.0.1", MONGO_PORT, 40):
        print("[error] MongoDB did not start in time — see", logfile)
    else:
        print("[info] MongoDB is up")
    return proc


def detect_soffice() -> str:
    for c in (
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    ):
        if Path(c).exists():
            return c
    return os.environ.get("SOFFICE_BIN", "soffice")


def open_browser_when_ready():
    if wait_port(HOST, PORT, 40):
        try:
            webbrowser.open(f"http://{HOST}:{PORT}")
        except Exception:
            pass


def main():
    base = base_dir()
    data = app_data()

    os.environ.setdefault("MONGO_URL", f"mongodb://127.0.0.1:{MONGO_PORT}")
    os.environ.setdefault("DB_NAME", "banetskaya_db")
    os.environ.setdefault("CORS_ORIGINS", "*")
    os.environ["SOFFICE_BIN"] = detect_soffice()

    mongo_proc = start_mongo(base, data / "data", data / "logs")

    import uvicorn
    import server  # reads env configured above at import time

    threading.Thread(target=open_browser_when_ready, daemon=True).start()

    print(f"[info] Banetskaya.by running at http://{HOST}:{PORT}  (закройте это окно чтобы остановить)")
    try:
        uvicorn.run(server.app, host=HOST, port=PORT, log_level="info")
    finally:
        if mongo_proc is not None:
            try:
                mongo_proc.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    main()
