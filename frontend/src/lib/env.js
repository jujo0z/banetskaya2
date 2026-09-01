// Detect whether the app runs as the local Windows desktop build (served from
// 127.0.0.1 by the bundled backend) vs. the public web version.
// In desktop mode the marketing/start "/welcome" page is skipped.
function computeIsDesktop() {
  try {
    // Most reliable: the bundled desktop backend (PyInstaller .exe) injects this
    // flag into index.html, so it is impossible to be mistaken for the web version.
    if (typeof window !== "undefined" && window.__IS_DESKTOP__ === true) {
      return true;
    }
    if (String(process.env.REACT_APP_IS_DESKTOP || "").toLowerCase() === "1" ||
        String(process.env.REACT_APP_IS_DESKTOP || "").toLowerCase() === "true") {
      return true;
    }
    const h = typeof window !== "undefined" ? window.location.hostname : "";
    return h === "127.0.0.1" || h === "localhost" || h === "::1";
  } catch (e) {
    return false;
  }
}

export const IS_DESKTOP = computeIsDesktop();
export const IS_WEB = !IS_DESKTOP;

// Optional download URL for the Windows installer (set at build time if available)
export const WINDOWS_DOWNLOAD_URL = process.env.REACT_APP_WINDOWS_DOWNLOAD_URL || "";
