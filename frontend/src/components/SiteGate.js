import React, { useState, useEffect, useRef } from "react";
import { siteGate, siteGateCheck } from "@/lib/apiClient";

const KEY = "bnk_gate_ok";

/**
 * Вход в браузерную часть сайта. Сервер выдаёт сессионную cookie (до закрытия браузера),
 * без неё /api не отдаёт данные. /tg не затрагивается.
 */
export default function SiteGate({ children }) {
  const [ok, setOk] = useState(false);
  const [checking, setChecking] = useState(true);
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const pwRef = useRef(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await siteGateCheck();
        if (!cancelled && r && (r.ok || r.enabled === false)) {
          try { sessionStorage.setItem(KEY, "1"); } catch (e) { /* ignore */ }
          setOk(true);
        }
      } catch (e) { /* показываем форму */ }
      if (!cancelled) setChecking(false);
    })();
    return () => { cancelled = true; };
  }, []);

  const submit = async (e) => {
    e?.preventDefault?.();
    if (busy) return;
    setBusy(true); setErr("");
    try {
      await siteGate(login.trim(), password);
      try { sessionStorage.setItem(KEY, "1"); } catch (er) { /* ignore */ }
      setPassword("");
      setOk(true);
    } catch (e2) {
      setErr(e2?.response?.data?.detail || "Неверный логин или пароль");
      if (pwRef.current) pwRef.current.focus();
    } finally { setBusy(false); }
  };

  if (ok) return children;
  if (checking) return <div className="min-h-screen w-full bg-slate-900" data-testid="gate-checking" />;

  return (
    <div className="min-h-screen w-full grid place-items-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 px-4">
      <div className="w-full max-w-sm rounded-3xl bg-white shadow-2xl ring-1 ring-black/5 p-7">
        <div className="flex flex-col items-center text-center mb-6">
          <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500 grid place-items-center text-white text-2xl font-black shadow-lg shadow-amber-300/40">B</div>
          <h1 className="mt-3 text-xl font-extrabold tracking-tight text-slate-800">Banetskaya.by</h1>
          <p className="text-xs text-slate-400 mt-1">Доступ по логину и паролю</p>
        </div>
        <div autoComplete="off" spellCheck={false}>
          {/* приманка против автозаполнения */}
          <input type="text" name="username_decoy" autoComplete="username"
            tabIndex={-1} aria-hidden="true"
            style={{ position: "absolute", opacity: 0, height: 0, width: 0, pointerEvents: "none" }} />
          <input type="password" name="password_decoy" autoComplete="new-password"
            tabIndex={-1} aria-hidden="true"
            style={{ position: "absolute", opacity: 0, height: 0, width: 0, pointerEvents: "none" }} />

          <label className="block text-[11px] font-semibold text-slate-400 mb-1">ЛОГИН</label>
          <input
            value={login}
            onChange={(e) => setLogin(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") submit(e); }}
            name="bnk_site_login"
            data-testid="gate-login"
            autoComplete="off"
            autoCapitalize="none"
            autoCorrect="off"
            className="w-full mb-3 rounded-xl bg-slate-50 ring-1 ring-slate-200 px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-orange-300"
            placeholder="Логин"
          />
          <label className="block text-[11px] font-semibold text-slate-400 mb-1">ПАРОЛЬ</label>
          <input
            ref={pwRef}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") submit(e); }}
            type="password"
            name="bnk_site_pass"
            data-testid="gate-password"
            autoComplete="new-password"
            className="w-full mb-1 rounded-xl bg-slate-50 ring-1 ring-slate-200 px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-orange-300"
            placeholder="Пароль"
          />
          {err && <div data-testid="gate-error" className="text-xs text-rose-600 mt-2 mb-1">{err}</div>}
          <button
            type="button"
            onClick={submit}
            data-testid="gate-submit"
            disabled={busy}
            className="mt-4 w-full py-3 rounded-2xl bg-gradient-to-r from-amber-400 to-orange-500 text-white font-bold shadow-md shadow-amber-300/40 disabled:opacity-60 active:scale-[0.99] transition"
          >
            {busy ? "Проверка…" : "Войти"}
          </button>
        </div>
      </div>
    </div>
  );
}
