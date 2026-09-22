import React, { useEffect, useState, useCallback, useMemo } from "react";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import {
  Building2, AlertTriangle, ChevronLeft, Search, Star, LogIn, LogOut,
  ClipboardCheck, Users, Bed, Sofa, CalendarDays, ShieldCheck, CheckCircle2,
  Sparkles, X, Trash2, Plus, Pencil,
} from "lucide-react";
import {
  publicFloors, publicFloor, publicBlock, publicSearch,
  login, logout, authMe, getToken, saveInspectionStarosta, deleteInspectionStarosta,
} from "@/lib/apiClient";

/* ------------------------------------------------------------------ */
/*  Telegram helpers (haptics, theme, native back button)             */
/* ------------------------------------------------------------------ */
const tg = () => (typeof window !== "undefined" ? window.Telegram?.WebApp : null);

function haptic(kind = "light") {
  try {
    const h = tg()?.HapticFeedback;
    if (!h) return;
    if (["light", "medium", "heavy", "rigid", "soft"].includes(kind)) h.impactOccurred(kind);
    else if (["success", "error", "warning"].includes(kind)) h.notificationOccurred(kind);
    else h.selectionChanged();
  } catch (e) { /* not in telegram */ }
}

const AREAS = [
  { key: "small_room", label: "Малая комната", icon: Bed },
  { key: "big_room", label: "Большая комната", icon: Users },
  { key: "common", label: "Общее пространство", icon: Sofa },
];

function todayStr() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${p(d.getDate())}.${p(d.getMonth() + 1)}.${d.getFullYear()}`;
}

/* date format helpers: ДД.ММ.ГГГГ <-> YYYY-MM-DD (native date input) */
function dmyToIso(s) {
  const m = /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/.exec((s || "").trim());
  if (!m) return "";
  return `${m[3]}-${m[2].padStart(2, "0")}-${m[1].padStart(2, "0")}`;
}
function isoToDmy(s) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec((s || "").trim());
  if (!m) return "";
  return `${m[3]}.${m[2]}.${m[1]}`;
}

/* grade → color tokens */
function gradeTone(g) {
  g = Number(g) || 0;
  if (g === 0) return { ring: "ring-slate-200", bg: "bg-slate-100", text: "text-slate-300", solid: "bg-slate-200" };
  if (g < 3) return { ring: "ring-rose-200", bg: "bg-gradient-to-br from-rose-500 to-rose-600", text: "text-white", solid: "bg-rose-500" };
  if (g === 3) return { ring: "ring-amber-200", bg: "bg-gradient-to-br from-amber-400 to-amber-500", text: "text-white", solid: "bg-amber-400" };
  return { ring: "ring-emerald-200", bg: "bg-gradient-to-br from-emerald-500 to-emerald-600", text: "text-white", solid: "bg-emerald-500" };
}

function inspFor(inspections, date) {
  if (!inspections) return null;
  return inspections.find((i) => i.date === date) || null;
}

/* pretty grade badge */
function Grade({ v, size = "md" }) {
  const t = gradeTone(v);
  const s = size === "lg" ? "h-12 w-12 text-lg" : size === "sm" ? "h-8 w-8 text-xs" : "h-9 w-9 text-sm";
  return (
    <span className={`${s} ${t.bg} ${t.text} rounded-2xl grid place-items-center font-extrabold ring-2 ${t.ring} shadow-sm`}>
      {v || "—"}
    </span>
  );
}

/* tiny colored dots summarising an inspection */
function Dots({ insp }) {
  return (
    <div className="flex gap-1">
      {AREAS.map((a) => {
        const t = gradeTone(insp ? insp[a.key] : 0);
        return <span key={a.key} className={`h-2 w-2 rounded-full ${t.solid}`} />;
      })}
    </div>
  );
}

/* motion presets */
const pageMotion = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.22, ease: [0.22, 1, 0.36, 1] },
};

/* ================================================================== */
/*  ROOT                                                              */
/* ================================================================== */
export default function TelegramApp() {
  const [view, setView] = useState("home");
  const [floors, setFloors] = useState(null); // null = loading
  const [floorNum, setFloorNum] = useState(null);
  const [floorData, setFloorData] = useState({ dates: [], blocks: [] });
  const [selectedDate, setSelectedDate] = useState("");
  const [block, setBlock] = useState(null);
  const [user, setUser] = useState(null);
  const [q, setQ] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    try {
      const w = tg();
      if (w) { w.ready(); w.expand(); w.setHeaderColor?.("#e11d48"); w.setBackgroundColor?.("#f6f6fa"); }
    } catch (e) { /* not in telegram */ }
    if (getToken()) authMe().then(setUser).catch(() => logout());
    publicFloors().then(setFloors).catch(() => setFloors([]));
  }, []);

  const goHome = useCallback(() => { haptic("soft"); setView("home"); }, []);

  const openFloor = useCallback(async (f) => {
    haptic("light");
    setFloorNum(f);
    setLoading(true);
    setView("floor");
    try {
      const d = await publicFloor(f);
      setFloorData(d);
      setSelectedDate(d.dates?.[0] || "");
    } catch (e) { setFloorData({ dates: [], blocks: [] }); }
    finally { setLoading(false); }
  }, []);

  const reloadFloor = useCallback(async () => {
    if (floorNum == null) return;
    try { setFloorData(await publicFloor(floorNum)); } catch (e) { /* ignore */ }
  }, [floorNum]);

  const openBlock = (b) => { haptic("light"); setBlock(b); setView("block"); };

  const doSearch = useCallback(async (text) => {
    setQ(text);
    if (!text.trim()) { setResults(null); return; }
    try { setResults(await publicSearch(text)); } catch (e) { setResults([]); }
  }, []);

  const onLogout = () => { haptic("medium"); logout(); setUser(null); toast.success("Вы вышли"); };

  const backTarget = view === "block" ? (floorNum != null ? "floor" : "home") : "home";

  /* native Telegram BackButton */
  useEffect(() => {
    const w = tg();
    const bb = w?.BackButton;
    if (!bb) return;
    const handler = () => { haptic("soft"); setView(backTarget); };
    if (view === "home") { bb.hide?.(); }
    else { bb.show?.(); bb.onClick?.(handler); }
    return () => { try { bb.offClick?.(handler); } catch (e) { /* noop */ } };
  }, [view, backTarget]);

  /* aggregate stats for hero */
  const stats = useMemo(() => {
    if (!floors) return null;
    const totalBlocks = floors.reduce((s, f) => s + (f.blocks || 0), 0);
    const problems = floors.reduce((s, f) => s + (f.problems || 0), 0);
    return { floors: floors.length, blocks: totalBlocks, problems };
  }, [floors]);

  return (
    <div className="min-h-screen text-slate-900 relative overflow-x-hidden"
      style={{ fontFamily: "Inter, system-ui, -apple-system, sans-serif", background: "#f6f6fa" }}>
      {/* decorative backdrop */}
      <div aria-hidden className="pointer-events-none fixed inset-x-0 top-0 h-72 -z-0"
        style={{ background: "radial-gradient(120% 90% at 50% -10%, rgba(225,29,72,0.16), rgba(225,29,72,0) 70%)" }} />

      {/* ---------- Header ---------- */}
      <header className="sticky top-0 z-30">
        <div className="bg-gradient-to-br from-[#e11d48] via-[#d61a5c] to-[#be185d] text-white px-4 pt-[max(16px,env(safe-area-inset-top))] pb-5 shadow-lg shadow-rose-500/20">
          <div className="max-w-lg mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-2xl bg-white/15 backdrop-blur ring-1 ring-white/20 grid place-items-center">
                <ClipboardCheck className="h-5 w-5" />
              </div>
              <div>
                <div className="font-extrabold text-[17px] leading-tight tracking-tight">Чистота общежития</div>
                <div className="text-[11px] text-white/75 mt-0.5">оценки блоков по этажам</div>
              </div>
            </div>
            {user ? (
              <button onClick={onLogout}
                className="flex items-center gap-1.5 text-xs bg-white/15 hover:bg-white/25 active:scale-95 ring-1 ring-white/20 rounded-full px-3 py-2 font-medium transition">
                <LogOut className="h-3.5 w-3.5" /> Выйти
              </button>
            ) : (
              <button data-testid="tg-login-open" onClick={() => { haptic("light"); setView("login"); }}
                className="flex items-center gap-1.5 text-xs bg-white text-rose-600 rounded-full px-3.5 py-2 font-semibold shadow-sm active:scale-95 transition">
                <LogIn className="h-3.5 w-3.5" /> Староста
              </button>
            )}
          </div>
          {user && (
            <div className="max-w-lg mx-auto mt-3 flex items-center gap-2 text-[12px] bg-white/12 ring-1 ring-white/15 rounded-xl px-3 py-2 w-fit">
              <ShieldCheck className="h-4 w-4" />
              <span className="font-medium">{user.full_name || user.username}</span>
              <span className="text-white/70">· этажи {(user.floors || []).join(", ") || "—"}</span>
            </div>
          )}
        </div>
      </header>

      {/* ---------- Body ---------- */}
      <main className="relative z-10 max-w-lg mx-auto px-4 py-4 pb-[max(28px,env(safe-area-inset-bottom))]">
        <AnimatePresence mode="wait">
          {view === "login" && (
            <motion.div key="login" {...pageMotion}>
              <LoginView onBack={goHome} onLoggedIn={(u) => { setUser(u); setView("home"); }} />
            </motion.div>
          )}

          {view === "home" && (
            <motion.div key="home" {...pageMotion} className="space-y-4">
              {/* search */}
              <div className="relative">
                <Search className="h-4 w-4 absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  data-testid="tg-search"
                  value={q}
                  onChange={(e) => doSearch(e.target.value)}
                  placeholder="Поиск по ФИО или блоку"
                  className="w-full rounded-2xl border-0 bg-white shadow-sm ring-1 ring-slate-200/70 pl-11 pr-10 py-3.5 text-sm focus:ring-2 focus:ring-rose-300 outline-none transition"
                />
                {q && (
                  <button onClick={() => { setQ(""); setResults(null); }}
                    className="absolute right-3 top-1/2 -translate-y-1/2 h-6 w-6 grid place-items-center rounded-full bg-slate-100 text-slate-400 active:scale-90">
                    <X className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>

              {results !== null ? (
                <div className="space-y-2" data-testid="tg-search-results">
                  <div className="text-xs text-slate-400 px-1">
                    {results.length ? `Найдено: ${results.length}` : "Ничего не найдено"}
                  </div>
                  {results.map((r, i) => (
                    <button key={i} onClick={() => openBlock(r.block)}
                      className="w-full text-left rounded-2xl bg-white shadow-sm ring-1 ring-slate-200/70 px-4 py-3.5 flex items-center justify-between active:scale-[0.99] transition">
                      <span className="font-semibold text-sm">{r.full_name}</span>
                      <span className="text-xs text-rose-600 bg-rose-50 rounded-full px-2.5 py-1 font-medium shrink-0 ml-2">блок {r.block}</span>
                    </button>
                  ))}
                </div>
              ) : (
                <>
                  {/* hero stats */}
                  {stats && (
                    <div className="rounded-3xl bg-white shadow-sm ring-1 ring-slate-200/70 p-4 grid grid-cols-3 divide-x divide-slate-100">
                      <Stat label="этажей" value={stats.floors} />
                      <Stat label="блоков" value={stats.blocks} />
                      <Stat label="проблем" value={stats.problems}
                        tone={stats.problems > 0 ? "rose" : "emerald"} />
                    </div>
                  )}

                  <Legend />

                  <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold px-1 pt-1">Этажи</div>

                  {floors === null ? (
                    <SkeletonList rows={5} />
                  ) : floors.length === 0 ? (
                    <Empty text="Нет данных по этажам" />
                  ) : (
                    <div className="space-y-2.5">
                      {floors.map((f, i) => (
                        <motion.button key={f.floor} data-testid={`tg-floor-${f.floor}`}
                          initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: Math.min(i * 0.03, 0.25) }}
                          onClick={() => openFloor(f.floor)}
                          className="w-full rounded-2xl bg-white shadow-sm ring-1 ring-slate-200/70 px-4 py-3.5 flex items-center justify-between active:scale-[0.99] transition">
                          <div className="flex items-center gap-3.5">
                            <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-rose-500 to-pink-600 grid place-items-center font-extrabold text-white text-lg shadow-sm shadow-rose-300/50">
                              {f.floor}
                            </div>
                            <div className="text-left">
                              <div className="font-bold leading-tight">{f.floor} этаж</div>
                              <div className="text-xs text-slate-400">{f.blocks} блоков</div>
                            </div>
                          </div>
                          {f.problems > 0 ? (
                            <span className="flex items-center gap-1 text-xs bg-rose-50 text-rose-600 rounded-full px-3 py-1.5 font-bold ring-1 ring-rose-100">
                              <AlertTriangle className="h-3.5 w-3.5" /> {f.problems}
                            </span>
                          ) : (
                            <span className="flex items-center gap-1 text-xs bg-emerald-50 text-emerald-600 rounded-full px-3 py-1.5 font-medium ring-1 ring-emerald-100">
                              <CheckCircle2 className="h-3.5 w-3.5" /> чисто
                            </span>
                          )}
                        </motion.button>
                      ))}
                    </div>
                  )}
                </>
              )}
            </motion.div>
          )}

          {view === "floor" && (
            <motion.div key="floor" {...pageMotion}>
              <FloorView
                floorNum={floorNum}
                floorData={floorData}
                selectedDate={selectedDate}
                setSelectedDate={setSelectedDate}
                loading={loading}
                onBack={goHome}
                onOpenBlock={openBlock}
              />
            </motion.div>
          )}

          {view === "block" && (
            <motion.div key="block" {...pageMotion}>
              <BlockView
                block={block}
                user={user}
                selectedDate={selectedDate}
                onBack={() => setView(floorNum != null ? "floor" : "home")}
                onSaved={reloadFloor}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

/* ================================================================== */
/*  Small pieces                                                      */
/* ================================================================== */
function Stat({ label, value, tone = "slate" }) {
  const color = tone === "rose" ? "text-rose-600" : tone === "emerald" ? "text-emerald-600" : "text-slate-900";
  return (
    <div className="px-2 text-center">
      <div className={`text-2xl font-extrabold leading-none ${color}`}>{value}</div>
      <div className="text-[11px] text-slate-400 mt-1">{label}</div>
    </div>
  );
}

function Legend() {
  const items = [
    { c: "bg-rose-500", t: "1–2 плохо" },
    { c: "bg-amber-400", t: "3 норма" },
    { c: "bg-emerald-500", t: "4–5 отлично" },
  ];
  return (
    <div className="flex items-center justify-center gap-4 text-[11px] text-slate-500">
      {items.map((i) => (
        <span key={i.t} className="flex items-center gap-1.5">
          <span className={`h-2.5 w-2.5 rounded-full ${i.c}`} /> {i.t}
        </span>
      ))}
    </div>
  );
}

function SkeletonList({ rows = 4 }) {
  return (
    <div className="space-y-2.5">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="rounded-2xl bg-white ring-1 ring-slate-200/70 px-4 py-3.5 flex items-center gap-3.5 animate-pulse">
          <div className="h-12 w-12 rounded-2xl bg-slate-100" />
          <div className="flex-1 space-y-2">
            <div className="h-3 w-24 bg-slate-100 rounded" />
            <div className="h-2.5 w-16 bg-slate-100 rounded" />
          </div>
          <div className="h-6 w-16 bg-slate-100 rounded-full" />
        </div>
      ))}
    </div>
  );
}

function Empty({ text }) {
  return (
    <div className="text-center py-12">
      <div className="h-14 w-14 mx-auto rounded-2xl bg-slate-100 grid place-items-center text-slate-300 mb-3">
        <Sparkles className="h-6 w-6" />
      </div>
      <div className="text-sm text-slate-400">{text}</div>
    </div>
  );
}

function BackBtn({ onBack, label = "Назад" }) {
  return (
    <button onClick={() => { haptic("soft"); onBack(); }}
      className="flex items-center gap-1 text-sm text-slate-500 font-medium active:scale-95 transition -ml-1 mb-3">
      <ChevronLeft className="h-4 w-4" /> {label}
    </button>
  );
}

function DateBar({ dates, selectedDate, setSelectedDate }) {
  if (!dates || dates.length === 0) {
    return <div className="text-xs text-slate-400 bg-white rounded-2xl px-4 py-3 ring-1 ring-slate-200/70">Проверок пока не было</div>;
  }
  return (
    <div>
      <div className="flex items-center gap-1.5 text-[11px] text-slate-400 font-semibold mb-2 px-1">
        <CalendarDays className="h-3.5 w-3.5" /> ДАТА ПРОВЕРКИ
      </div>
      <div className="flex gap-2 overflow-x-auto pb-1 -mx-1 px-1 no-scrollbar">
        {dates.map((d) => (
          <button key={d} data-testid={`tg-date-${d}`}
            onClick={() => { haptic("selection"); setSelectedDate(d); }}
            className={`shrink-0 px-3.5 py-2 rounded-xl text-sm font-semibold transition active:scale-95 ${
              selectedDate === d ? "bg-slate-900 text-white shadow-md" : "bg-white text-slate-600 ring-1 ring-slate-200/70"
            }`}>
            {d}
          </button>
        ))}
      </div>
    </div>
  );
}

/* ================================================================== */
/*  Floor view                                                        */
/* ================================================================== */
function FloorView({ floorNum, floorData, selectedDate, setSelectedDate, loading, onBack, onOpenBlock }) {
  return (
    <div>
      <BackBtn onBack={onBack} label="Этажи" />
      <div className="flex items-baseline gap-2 mb-3">
        <div className="text-2xl font-extrabold tracking-tight">{floorNum} этаж</div>
        <div className="text-sm text-slate-400">{floorData.blocks?.length || 0} блоков</div>
      </div>
      <DateBar dates={floorData.dates} selectedDate={selectedDate} setSelectedDate={setSelectedDate} />
      <div className="mt-3">
        {loading ? (
          <div className="grid grid-cols-2 gap-2.5">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="rounded-2xl bg-white ring-1 ring-slate-200/70 p-3.5 h-28 animate-pulse" />
            ))}
          </div>
        ) : floorData.blocks?.length ? (
          <div className="grid grid-cols-2 gap-2.5">
            {floorData.blocks.map((b, i) => {
              const insp = inspFor(b.inspections, selectedDate);
              const problem = insp?.problem;
              return (
                <motion.button key={b.block} data-testid={`tg-block-${b.block}`}
                  initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: Math.min(i * 0.02, 0.2) }}
                  onClick={() => onOpenBlock(b.block)}
                  className={`rounded-2xl p-3.5 text-left active:scale-[0.97] transition shadow-sm ring-1 ${
                    problem ? "bg-rose-50 ring-rose-200" : "bg-white ring-slate-200/70"
                  }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 font-extrabold text-lg">
                      <Building2 className={`h-4 w-4 ${problem ? "text-rose-500" : "text-rose-300"}`} />
                      {b.block}
                    </div>
                    {problem ? <AlertTriangle className="h-4 w-4 text-rose-500" /> : insp && <CheckCircle2 className="h-4 w-4 text-emerald-400" />}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
                    <Users className="h-3 w-3" /> {b.people} чел.
                  </div>
                  {insp ? (
                    <div className="flex gap-1.5 mt-3">
                      {AREAS.map((a) => <Grade key={a.key} v={insp[a.key]} size="sm" />)}
                    </div>
                  ) : (
                    <div className="text-[11px] text-slate-300 mt-3">нет оценки на дату</div>
                  )}
                </motion.button>
              );
            })}
          </div>
        ) : (
          <Empty text="На этаже нет блоков" />
        )}
      </div>
    </div>
  );
}

/* ================================================================== */
/*  Login view                                                        */
/* ================================================================== */
function LoginView({ onBack, onLoggedIn }) {
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async () => {
    if (!u.trim() || !p.trim()) { toast.error("Введите логин и пароль"); return; }
    setBusy(true);
    try {
      const d = await login(u.trim(), p.trim());
      haptic("success"); toast.success("Добро пожаловать!"); onLoggedIn(d.user);
    } catch (e) { haptic("error"); toast.error(e?.response?.data?.detail || "Ошибка входа"); }
    finally { setBusy(false); }
  };
  return (
    <div>
      <BackBtn onBack={onBack} />
      <div className="rounded-3xl bg-white shadow-sm ring-1 ring-slate-200/70 p-6 space-y-4">
        <div className="h-16 w-16 rounded-3xl bg-gradient-to-br from-rose-500 to-pink-600 grid place-items-center text-white mx-auto shadow-lg shadow-rose-300/50">
          <ShieldCheck className="h-8 w-8" />
        </div>
        <div className="text-center">
          <h2 className="font-extrabold text-lg">Вход для старосты</h2>
          <p className="text-[12px] text-slate-400 mt-1">Учащиеся смотрят оценки без входа</p>
        </div>
        <input data-testid="tg-login-user" value={u} onChange={(e) => setU(e.target.value)} placeholder="Логин"
          autoCapitalize="none" autoCorrect="off"
          className="w-full rounded-2xl bg-slate-50 ring-1 ring-slate-200 px-4 py-3.5 text-sm focus:ring-2 focus:ring-rose-300 outline-none transition" />
        <input data-testid="tg-login-pass" type="password" value={p} onChange={(e) => setP(e.target.value)} placeholder="Пароль"
          onKeyDown={(e) => e.key === "Enter" && submit()}
          className="w-full rounded-2xl bg-slate-50 ring-1 ring-slate-200 px-4 py-3.5 text-sm focus:ring-2 focus:ring-rose-300 outline-none transition" />
        <button data-testid="tg-login-submit" onClick={submit} disabled={busy}
          className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-rose-500 to-pink-600 text-white font-bold shadow-md shadow-rose-300/50 disabled:opacity-60 active:scale-[0.99] transition">
          {busy ? "Вход…" : "Войти"}
        </button>
      </div>
    </div>
  );
}

/* ================================================================== */
/*  Block view                                                        */
/* ================================================================== */
function BlockView({ block, user, selectedDate, onBack, onSaved }) {
  const [data, setData] = useState(null);
  const [date, setDate] = useState(selectedDate || "");
  const canGrade = user && (user.role === "admin" || (user.floors || []).includes(Math.floor(Number(block) / 100)));

  const reload = useCallback(async () => {
    try {
      const d = await publicBlock(block);
      setData(d);
      return d;
    } catch (e) { const empty = { rooms: [], inspections: [] }; setData(empty); return empty; }
  }, [block]);

  useEffect(() => {
    reload().then((d) => setDate((prev) => prev || d.inspections?.[0]?.date || todayStr()));
  }, [reload]);
  useEffect(() => { if (selectedDate) setDate(selectedDate); }, [selectedDate]);

  const current = inspFor(data?.inspections, date);
  const gradeByKey = (k) => (current ? current[k] : 0);

  const handleSaved = async (savedDate) => {
    await reload();
    if (savedDate) setDate(savedDate);
    onSaved?.();
  };
  const handleDeleted = async () => {
    const d = await reload();
    setDate(d.inspections?.[0]?.date || todayStr());
    onSaved?.();
  };

  return (
    <div>
      <BackBtn onBack={onBack} />

      {/* hero */}
      <div className="rounded-3xl bg-gradient-to-br from-[#e11d48] via-[#d61a5c] to-[#be185d] text-white p-5 shadow-lg shadow-rose-500/25">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-2xl bg-white/15 ring-1 ring-white/20 grid place-items-center"><Building2 className="h-6 w-6" /></div>
            <div>
              <div className="font-extrabold text-2xl leading-none tracking-tight">Блок {block}</div>
              {data?.elder && <div className="text-xs text-white/85 mt-1.5 flex items-center gap-1"><Star className="h-3 w-3" /> {data.elder}</div>}
            </div>
          </div>
          {current?.problem && (
            <div className="text-[11px] bg-white/20 ring-1 ring-white/25 rounded-full px-3 py-1.5 font-bold flex items-center gap-1">
              <AlertTriangle className="h-3.5 w-3.5" /> проблема
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {data?.inspections?.length > 0 && (
          <DateBar dates={data.inspections.map((i) => i.date)} selectedDate={date} setSelectedDate={setDate} />
        )}

        {/* rooms */}
        {(data?.rooms || []).map((room) => {
          const Icon = AREAS.find((a) => a.key === room.grade_key)?.icon || Sofa;
          return (
            <div key={room.type} data-testid={`tg-room-${room.type}`} className="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200/70 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="h-10 w-10 rounded-xl bg-rose-50 grid place-items-center text-rose-500"><Icon className="h-5 w-5" /></div>
                  <div>
                    <div className="font-bold text-sm">{room.label}</div>
                    <div className="text-[11px] text-slate-400">
                      {room.type === "common" ? "проживающих нет" : `${room.occupied} из ${room.capacity} мест`}
                    </div>
                  </div>
                </div>
                <Grade v={gradeByKey(room.grade_key)} size="lg" />
              </div>
              {room.people.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {room.people.map((p, i) => (
                    <span key={i} className="text-xs bg-slate-50 ring-1 ring-slate-200/70 rounded-lg px-2.5 py-1.5 font-medium">{p.full_name}</span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
        {(!data) && <SkeletonList rows={3} />}
        {(data && (data.rooms || []).length === 0) && <Empty text="Нет данных по блоку" />}

        {current?.note && (
          <div className="text-xs text-slate-600 bg-amber-50 rounded-2xl px-4 py-3 ring-1 ring-amber-100 flex gap-2">
            <span className="font-semibold text-amber-700">Примечание:</span> {current.note}
          </div>
        )}

        {canGrade && (
          <GradeEditor
            block={block}
            initialDate={date}
            inspections={data?.inspections || []}
            onSaved={handleSaved}
            onDeleted={handleDeleted}
          />
        )}
        {user && !canGrade && (
          <div className="text-xs text-amber-700 bg-amber-50 rounded-2xl p-3 ring-1 ring-amber-100">
            У вас нет доступа к {Math.floor(Number(block) / 100)} этажу — только просмотр.
          </div>
        )}
      </div>
    </div>
  );
}

/* ================================================================== */
/*  Grade editor                                                      */
/* ================================================================== */
function GradeEditor({ block, initialDate, inspections, onSaved, onDeleted }) {
  const [date, setDate] = useState(initialDate || todayStr());
  const [g, setG] = useState({ small_room: 0, big_room: 0, common: 0 });
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [confirmDel, setConfirmDel] = useState(false);

  // find an existing inspection for the currently chosen date
  const existing = (inspections || []).find((i) => i.date === date) || null;

  useEffect(() => { setDate(initialDate || todayStr()); }, [initialDate]);

  // whenever the chosen date (or list) changes: prefill from that date's
  // inspection if it exists, otherwise start a blank NEW check
  useEffect(() => {
    const ex = (inspections || []).find((i) => i.date === date) || null;
    if (ex) { setG({ small_room: ex.small_room, big_room: ex.big_room, common: ex.common }); setNote(ex.note || ""); }
    else { setG({ small_room: 0, big_room: 0, common: 0 }); setNote(""); }
    setConfirmDel(false);
  }, [date, inspections]);

  const setGrade = (key, n) => { haptic("light"); setG((s) => ({ ...s, [key]: n })); };

  const newCheck = () => { haptic("selection"); setDate(todayStr()); setConfirmDel(false); };

  const save = async () => {
    if (!dmyToIso(date)) { haptic("warning"); toast.error("Выберите дату проверки"); return; }
    if (!g.small_room || !g.big_room || !g.common) { haptic("warning"); toast.error("Проставьте все три оценки"); return; }
    setBusy(true);
    try {
      await saveInspectionStarosta({ block, date, ...g, note });
      haptic("success");
      toast.success(existing ? "Проверка обновлена" : "Новая проверка сохранена");
      onSaved?.(date);
    } catch (e) { haptic("error"); toast.error(e?.response?.data?.detail || "Не удалось сохранить"); }
    finally { setBusy(false); }
  };

  const doDelete = async () => {
    if (!existing) return;
    setBusy(true);
    try {
      await deleteInspectionStarosta(existing.id);
      haptic("success");
      toast.success(`Проверка за ${date} удалена`);
      setConfirmDel(false);
      onDeleted?.();
    } catch (e) { haptic("error"); toast.error(e?.response?.data?.detail || "Не удалось удалить"); }
    finally { setBusy(false); }
  };

  return (
    <div className="rounded-3xl bg-white shadow-sm ring-1 ring-rose-100 p-5 space-y-4" data-testid="tg-grade-editor">
      <div className="flex items-center justify-between">
        <div className="font-bold text-sm flex items-center gap-2">
          <span className="h-7 w-7 rounded-lg bg-rose-50 grid place-items-center text-rose-500">
            {existing ? <Pencil className="h-4 w-4" /> : <ClipboardCheck className="h-4 w-4" />}
          </span>
          {existing ? "Редактировать проверку" : "Новая проверка"}
        </div>
        <button onClick={newCheck}
          className="flex items-center gap-1 text-xs font-semibold text-rose-600 bg-rose-50 rounded-full px-3 py-1.5 ring-1 ring-rose-100 active:scale-95 transition">
          <Plus className="h-3.5 w-3.5" /> Новая
        </button>
      </div>

      <div>
        <div className="text-[11px] text-slate-400 mb-1.5 font-semibold">ДАТА ПРОВЕРКИ</div>
        <input type="date" data-testid="tg-grade-date" value={dmyToIso(date)}
          onChange={(e) => setDate(isoToDmy(e.target.value) || todayStr())}
          className="rounded-xl bg-slate-50 ring-1 ring-slate-200 px-3 py-2.5 text-sm focus:ring-2 focus:ring-rose-300 outline-none" />
        <div className="text-[11px] text-slate-400 mt-1.5">
          {existing
            ? "На эту дату уже есть проверка — сохранение обновит её."
            : "Новая дата — создаст отдельную проверку (можно вчера/сегодня/завтра)."}
        </div>
      </div>

      {AREAS.map((a) => (
        <div key={a.key}>
          <div className="text-sm flex items-center gap-2 mb-2 font-medium">
            <a.icon className="h-4 w-4 text-slate-400" /> {a.label}
          </div>
          <div className="grid grid-cols-5 gap-1.5">
            {[1, 2, 3, 4, 5].map((n) => {
              const active = Number(g[a.key]) === n;
              const t = gradeTone(n);
              return (
                <button key={n} onClick={() => setGrade(a.key, n)}
                  className={`h-11 rounded-xl font-extrabold text-sm ring-2 transition active:scale-95 ${
                    active ? `${t.bg} ${t.text} ${t.ring} shadow-md scale-105` : "bg-white text-slate-400 ring-slate-200"
                  }`}>{n}</button>
              );
            })}
          </div>
        </div>
      ))}

      <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={2} placeholder="Примечание (необязательно)"
        className="w-full rounded-xl bg-slate-50 ring-1 ring-slate-200 px-3 py-2.5 text-sm resize-none focus:ring-2 focus:ring-rose-300 outline-none" />

      <button data-testid="tg-grade-save" onClick={save} disabled={busy}
        className="w-full py-3.5 rounded-2xl bg-gradient-to-r from-rose-500 to-pink-600 text-white font-bold shadow-md shadow-rose-300/50 disabled:opacity-60 active:scale-[0.99] transition">
        {busy ? "Сохранение…" : existing ? "Сохранить изменения" : "Сохранить проверку"}
      </button>

      {existing && (
        confirmDel ? (
          <div className="rounded-2xl bg-rose-50 ring-1 ring-rose-100 p-3 space-y-2.5" data-testid="tg-grade-delete-confirm">
            <div className="text-sm text-rose-700 font-medium text-center">Удалить проверку за {date}?</div>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={() => setConfirmDel(false)} disabled={busy}
                className="py-2.5 rounded-xl bg-white ring-1 ring-slate-200 text-slate-600 font-semibold text-sm active:scale-95 transition">
                Отмена
              </button>
              <button data-testid="tg-grade-delete-yes" onClick={doDelete} disabled={busy}
                className="py-2.5 rounded-xl bg-rose-600 text-white font-semibold text-sm active:scale-95 transition disabled:opacity-60">
                {busy ? "Удаление…" : "Удалить"}
              </button>
            </div>
          </div>
        ) : (
          <button data-testid="tg-grade-delete" onClick={() => { haptic("medium"); setConfirmDel(true); }}
            className="w-full py-2.5 rounded-2xl bg-white ring-1 ring-rose-200 text-rose-600 font-semibold text-sm flex items-center justify-center gap-2 active:scale-[0.99] transition">
            <Trash2 className="h-4 w-4" /> Удалить проверку за {date}
          </button>
        )
      )}
    </div>
  );
}
