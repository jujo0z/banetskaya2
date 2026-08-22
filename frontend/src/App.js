import "@/App.css";
import React, { useEffect } from "react";
import { BrowserRouter, Routes, Route, useLocation, useNavigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import Generate from "@/pages/Generate";
import History from "@/pages/History";
import Settings from "@/pages/Settings";
import BlankOverlay from "@/pages/BlankOverlay";
import FullPrint from "@/pages/FullPrint";
import Landing from "@/pages/Landing";
import { IS_WEB, IS_DESKTOP } from "@/lib/env";

// Desktop build only: ping the local backend so it stays alive while the app
// window is open. When the window closes, pings stop and the bundled server
// shuts itself down (see start_idle_watchdog in the backend).
function useDesktopKeepAlive() {
  useEffect(() => {
    if (!IS_DESKTOP) return;
    const base = process.env.REACT_APP_BACKEND_URL || "";
    const ping = () => fetch(`${base}/api/_ping`).catch(() => {});
    ping();
    const id = setInterval(ping, 5000);
    return () => clearInterval(id);
  }, []);
}

// In the WEB version, first-time visitors at "/" are sent to the "/welcome"
// start page (installer on top, "start working" below). The desktop build
// (127.0.0.1) skips this entirely and opens straight into the app.
function EntryGate() {
  const loc = useLocation();
  const nav = useNavigate();
  useEffect(() => {
    if (!IS_WEB) return;
    let entered = false;
    try {
      entered = sessionStorage.getItem("bnk_entered") === "1";
    } catch (e) {
      entered = false;
    }
    if (!entered && loc.pathname === "/") {
      nav("/welcome", { replace: true });
    }
  }, [loc.pathname, nav]);
  return null;
}

function App() {
  useDesktopKeepAlive();
  return (
    <BrowserRouter>
      <EntryGate />
      <Routes>
        <Route path="/welcome" element={<Landing />} />
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="generate" element={<Generate />} />
          <Route path="history" element={<History />} />
          <Route path="blank" element={<BlankOverlay />} />
          <Route path="full-print" element={<FullPrint />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
      <Toaster theme="dark" position="top-right" richColors />
    </BrowserRouter>
  );
}

export default App;
