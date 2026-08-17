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
import Landing from "@/pages/Landing";
import { IS_WEB } from "@/lib/env";

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
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
      <Toaster theme="dark" position="top-right" richColors />
    </BrowserRouter>
  );
}

export default App;
