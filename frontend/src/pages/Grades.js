import React, { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { Building2, AlertTriangle, RefreshCw, Trash2, UserPlus, Star, ChevronLeft, UtensilsCrossed, CalendarDays } from "lucide-react";
import {
  residentsFloors, residentsFloor, residentsBlock,
  listInspections, saveInspectionAdmin, deleteInspection,
  setBlockElder, residentCreate,
  publicKitchens, publicKitchen,
} from "@/lib/apiClient";

const GRADE_LABELS = { small_room: "Малая комната", big_room: "Большая комната", common: "Общее пространство" };

function todayStr() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${p(d.getDate())}.${p(d.getMonth() + 1)}.${d.getFullYear()}`;
}

function _dmyToIso(s) {
  const m = /^(\d{1,2})\.(\d{1,2})\.(\d{4})$/.exec((s || "").trim());
  if (!m) return "";
  return `${m[3]}-${m[2].padStart(2, "0")}-${m[1].padStart(2, "0")}`;
}
function _isoToDmy(s) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec((s || "").trim());
  if (!m) return "";
  return `${m[3]}.${m[2]}.${m[1]}`;
}

function gradeColor(g) {
  g = Number(g) || 0;
  if (g === 0) return "bg-slate-100 text-slate-400 border-slate-200";
  if (g < 3) return "bg-red-500 text-white border-red-600";
  if (g === 3) return "bg-amber-400 text-white border-amber-500";
  return "bg-emerald-500 text-white border-emerald-600";
}

function GradePicker({ value, onChange }) {
  return (
    <div className="flex gap-1.5">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          onClick={() => onChange(n)}
          className={`h-10 w-10 rounded-lg border font-bold text-sm transition-all ${
            Number(value) === n
              ? gradeColor(n) + " scale-110 shadow"
              : "bg-white text-slate-600 border-slate-200 hover:border-pink-300"
          }`}
        >
          {n}
        </button>
      ))}
    </div>
  );
}

export default function Grades() {
  const [floors, setFloors] = useState([]);
  const [activeFloor, setActiveFloor] = useState(null);
  const [blocks, setBlocks] = useState([]);
  const [activeBlock, setActiveBlock] = useState(null);
  const [tab, setTab] = useState("blocks");

  const loadFloors = useCallback(async () => {
    try {
      const d = await residentsFloors();
      setFloors(d.floors || []);
    } catch (e) { /* ignore */ }
  }, []);

  const loadFloor = useCallback(async (floor) => {
    try {
      const d = await residentsFloor(floor);
      setBlocks((d.blocks || []).filter((b) => b.people > 0 || b.latest));
    } catch (e) { /* ignore */ }
  }, []);

  useEffect(() => { loadFloors(); }, [loadFloors]);

  useEffect(() => {
    if (activeFloor == null) return;
    loadFloor(activeFloor);
    const id = setInterval(() => loadFloor(activeFloor), 10000);
    return () => clearInterval(id);
  }, [activeFloor, loadFloor]);

  const openFloor = (f) => { setActiveBlock(null); setActiveFloor(f); };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-3xl font-bold tracking-tight">Оценки за чистоту</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Проверки блоков по этажам. Блок краснеет, если любая оценка ниже 3.
          </p>
        </div>
        <button onClick={loadFloors} className="flex items-center gap-2 text-sm text-muted-foreground hover:text-slate-900">
          <RefreshCw className="h-4 w-4" /> Обновить
        </button>
      </div>

      <div className="flex gap-1 bg-slate-100 rounded-xl p-1 w-fit">
        <button onClick={() => setTab("blocks")} className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition ${tab === "blocks" ? "bg-white text-rose-600 shadow-sm" : "text-slate-500"}`}>
          <Building2 className="h-4 w-4" /> Блоки
        </button>
        <button onClick={() => setTab("kitchens")} className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-semibold transition ${tab === "kitchens" ? "bg-white text-orange-600 shadow-sm" : "text-slate-500"}`}>
          <UtensilsCrossed className="h-4 w-4" /> Кухни
        </button>
      </div>

      {tab === "kitchens" && <KitchensReport />}

      {tab === "blocks" && (
      <div className="space-y-6">
      {/* Floors */}
      <div className="flex flex-wrap gap-2" data-testid="floors-row">
        {floors.map((f) => (
          <button
            key={f.floor}
            data-testid={`floor-btn-${f.floor}`}
            onClick={() => openFloor(f.floor)}
            className={`px-4 py-2 rounded-xl border text-sm font-semibold transition-all ${
              activeFloor === f.floor
                ? "bg-gradient-to-r from-[#F43F5E] to-[#DB2777] text-white border-transparent shadow"
                : "bg-white border-slate-200 hover:border-pink-300"
            }`}
          >
            {f.floor} этаж
            <span className="ml-2 text-xs opacity-70">{f.people} чел.</span>
          </button>
        ))}
        {floors.length === 0 && (
          <div className="text-sm text-muted-foreground">
            Нет данных о заселении. Загрузите жильцов в разделе «Заселение по этажам».
          </div>
        )}
      </div>

      {activeFloor != null && !activeBlock && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3" data-testid="blocks-grid">
          {blocks.map((b) => (
            <button
              key={b.block}
              data-testid={`block-card-${b.block}`}
              onClick={() => setActiveBlock(b.block)}
              className={`text-left rounded-2xl border p-4 transition-all hover:shadow-lg ${
                b.problem
                  ? "bg-red-50 border-red-400 ring-2 ring-red-400/40"
                  : "bg-white border-slate-200 hover:border-pink-300"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 font-heading text-xl font-bold">
                  <Building2 className={`h-5 w-5 ${b.problem ? "text-red-500" : "text-pink-400"}`} />
                  {b.block}
                </div>
                {b.problem && <AlertTriangle className="h-5 w-5 text-red-500" />}
              </div>
              <div className="text-xs text-muted-foreground mt-1">{b.people} чел.</div>
              {b.elder && (
                <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1 truncate">
                  <Star className="h-3 w-3 text-amber-400" /> {b.elder}
                </div>
              )}
              {b.latest ? (
                <div className="flex gap-1.5 mt-3">
                  {["small_room", "big_room", "common"].map((k) => (
                    <span key={k} className={`h-7 w-7 rounded-md border grid place-items-center text-xs font-bold ${gradeColor(b.latest[k])}`}>
                      {b.latest[k] || "—"}
                    </span>
                  ))}
                </div>
              ) : (
                <div className="text-[11px] text-slate-400 mt-3">Нет проверок</div>
              )}
            </button>
          ))}
        </div>
      )}

      {activeBlock && (
        <BlockDetail
          block={activeBlock}
          onBack={() => { setActiveBlock(null); loadFloor(activeFloor); }}
        />
      )}
      </div>
      )}
    </div>
  );
}

function _kgradeColor(g) {
  g = Number(g) || 0;
  if (g === 0) return "bg-slate-100 text-slate-400 border-slate-200";
  if (g < 3) return "bg-red-500 text-white border-red-600";
  if (g === 3) return "bg-amber-400 text-white border-amber-500";
  return "bg-emerald-500 text-white border-emerald-600";
}

function KitchensReport() {
  const [data, setData] = useState(null);
  const [active, setActive] = useState(null); // kitchen code
  const [detail, setDetail] = useState(null);

  const load = useCallback(async () => {
    try { setData(await publicKitchens()); } catch (e) { setData({ floors: [] }); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const openKitchen = async (k) => {
    setActive(k); setDetail(null);
    try { setDetail(await publicKitchen(k)); } catch (e) { setDetail({ kitchen: k, rows: [], inspections: [] }); }
  };

  if (active != null) {
    const d = detail;
    return (
      <div className="space-y-5">
        <button onClick={() => { setActive(null); setDetail(null); }} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-slate-900">
          <ChevronLeft className="h-4 w-4" /> Ко всем кухням
        </button>
        <div className="flex items-center gap-3">
          <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 grid place-items-center text-white font-bold">{active}</div>
          <div>
            <h2 className="font-heading text-2xl font-bold capitalize">{d?.pos || ""} кухня {active}</h2>
            <p className="text-xs text-muted-foreground">{Math.floor(active / 10)} этаж · дежурства и оценки</p>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-5">
          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <h3 className="font-semibold mb-3">Оценки за чистоту</h3>
            {!d && <div className="text-sm text-muted-foreground">Загрузка…</div>}
            {d && (d.inspections || []).length === 0 && <div className="text-sm text-muted-foreground">Проверок пока не было.</div>}
            <div className="space-y-2">
              {(d?.inspections || []).map((i) => (
                <div key={i.id} className={`flex items-center gap-3 rounded-xl border px-4 py-2.5 ${1 <= i.grade && i.grade <= 2 ? "bg-red-50 border-red-300" : "bg-slate-50 border-slate-200"}`}>
                  <span className={`h-8 w-8 rounded-md border grid place-items-center text-sm font-bold shrink-0 ${_kgradeColor(i.grade)}`}>{i.grade || "—"}</span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-slate-500 shrink-0">{i.date}</span>
                      <span className="text-sm font-semibold truncate">{i.student_name || i.resident_full_name || "— (за день)"}{i.student_unit ? ` · ${i.student_unit}` : ""}</span>
                    </div>
                    {i.reason && <div className="text-xs text-red-600 truncate">{i.reason}</div>}
                    {i.note && <div className="text-xs text-muted-foreground italic truncate">{i.note}</div>}
                  </div>
                  <span className="ml-auto text-[11px] text-slate-400 shrink-0">{i.created_by}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5">
            <h3 className="font-semibold mb-3 flex items-center gap-2"><CalendarDays className="h-4 w-4 text-orange-500" /> График дежурств</h3>
            {!d && <div className="text-sm text-muted-foreground">Загрузка…</div>}
            {d && (d.rows || []).length === 0 && <div className="text-sm text-muted-foreground">График не загружен. Староста загружает его через Telegram-бот.</div>}
            <div className="space-y-1.5 max-h-[420px] overflow-auto">
              {(d?.rows || []).map((r, idx) => (
                <div key={idx} className="rounded-lg bg-slate-50 border border-slate-100 px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-bold text-orange-600 bg-orange-50 rounded px-1.5 py-0.5">{r.unit || "—"}</span>
                    <span className="text-sm font-medium truncate">{r.name || "—"}</span>
                  </div>
                  {r.dates?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {r.dates.map((dt, i) => <span key={i} className="text-[11px] bg-white border border-slate-200 rounded px-1.5 py-0.5 text-slate-500">{dt}</span>)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {data === null && <div className="text-sm text-muted-foreground">Загрузка…</div>}
      {data && (data.floors || []).length === 0 && <div className="text-sm text-muted-foreground">Нет данных о кухнях.</div>}
      {(data?.floors || []).map((f) => (
        <div key={f.floor}>
          <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-2">{f.floor} этаж</div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {f.kitchens.map((k) => (
              <button key={k.kitchen} onClick={() => openKitchen(k.kitchen)}
                className={`text-left rounded-2xl border p-4 transition-all hover:shadow-lg ${k.problem ? "bg-red-50 border-red-400 ring-2 ring-red-400/40" : "bg-white border-slate-200 hover:border-orange-300"}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 font-heading text-lg font-bold">
                    <UtensilsCrossed className={`h-5 w-5 ${k.problem ? "text-red-500" : "text-orange-400"}`} /> {k.kitchen}
                  </div>
                  {k.latest_grade > 0 && <span className={`h-7 w-7 rounded-md border grid place-items-center text-xs font-bold ${_kgradeColor(k.latest_grade)}`}>{k.latest_grade}</span>}
                </div>
                <div className="text-xs text-muted-foreground mt-1 capitalize">{k.pos}</div>
                <div className="text-[11px] text-slate-400 mt-1">{k.has_schedule ? "график загружен" : "график не загружен"}</div>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function BlockDetail({ block, onBack }) {
  const [residents, setResidents] = useState([]);
  const [elder, setElder] = useState("");
  const [inspections, setInspections] = useState([]);
  const [date, setDate] = useState(todayStr());
  const [grades, setGrades] = useState({ small_room: 0, big_room: 0, common: 0 });
  const [note, setNote] = useState("");
  const [saving, setSaving] = useState(false);
  // add resident
  const [newName, setNewName] = useState("");
  const [newRoom, setNewRoom] = useState("2");

  const reload = useCallback(async () => {
    try {
      const b = await residentsBlock(block);
      const flat = [];
      (b.rooms || []).forEach((r) => (r.people || []).forEach((p) => flat.push(p)));
      setResidents(flat);
      const insp = await listInspections({ block });
      setInspections(insp.inspections || []);
    } catch (e) { /* ignore */ }
  }, [block]);

  useEffect(() => {
    reload();
    // load elder
    import("@/lib/apiClient").then((m) => m.publicBlock(block).then((d) => setElder(d.elder || "")).catch(() => {}));
  }, [block, reload]);

  // prefill grade form when date matches an existing inspection
  useEffect(() => {
    const found = inspections.find((i) => i.date === date);
    if (found) {
      setGrades({ small_room: found.small_room, big_room: found.big_room, common: found.common });
      setNote(found.note || "");
    }
  }, [date, inspections]);

  const save = async () => {
    if (!grades.small_room || !grades.big_room || !grades.common) {
      toast.error("Проставьте все три оценки (1–5)");
      return;
    }
    setSaving(true);
    try {
      await saveInspectionAdmin({ block, date, ...grades, note });
      toast.success("Оценки сохранены");
      await reload();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Не удалось сохранить");
    } finally { setSaving(false); }
  };

  const del = async (id) => {
    try { await deleteInspection(id); toast.success("Проверка удалена"); await reload(); }
    catch (e) { toast.error("Не удалось удалить"); }
  };

  const saveElder = async (name) => {
    setElder(name);
    try { await setBlockElder(block, name); toast.success("Староста блока сохранён"); }
    catch (e) { toast.error("Не удалось сохранить старосту"); }
  };

  const addResident = async () => {
    if (!newName.trim()) { toast.error("Укажите ФИО"); return; }
    try {
      await residentCreate({ block, room: newRoom, full_name: newName.trim() });
      toast.success("Жилец добавлен");
      setNewName("");
      await reload();
    } catch (e) { toast.error("Не удалось добавить"); }
  };

  return (
    <div className="space-y-5">
      <button onClick={onBack} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-slate-900">
        <ChevronLeft className="h-4 w-4" /> Назад к блокам
      </button>

      <div className="flex items-center gap-3">
        <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-[#F43F5E] to-[#DB2777] grid place-items-center text-white">
          <Building2 className="h-5 w-5" />
        </div>
        <div>
          <h2 className="font-heading text-2xl font-bold">Блок {block}</h2>
          <p className="text-xs text-muted-foreground">{residents.length} проживающих</p>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-5">
        {/* Grade form */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-4">
          <h3 className="font-semibold">Выставить оценки</h3>
          <div>
            <label className="text-xs text-muted-foreground">Дата проверки</label>
            <input
              type="date"
              data-testid="grade-date"
              value={_dmyToIso(date)}
              onChange={(e) => setDate(_isoToDmy(e.target.value) || todayStr())}
              className="mt-1 w-44 rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </div>
          {["small_room", "big_room", "common"].map((k) => (
            <div key={k} className="flex items-center justify-between">
              <span className="text-sm">{GRADE_LABELS[k]}</span>
              <GradePicker value={grades[k]} onChange={(n) => setGrades((g) => ({ ...g, [k]: n }))} />
            </div>
          ))}
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Примечание (необязательно)"
            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm resize-none"
            rows={2}
          />
          <button
            data-testid="save-grades-btn"
            onClick={save}
            disabled={saving}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-[#F43F5E] to-[#DB2777] text-white font-semibold disabled:opacity-60"
          >
            {saving ? "Сохранение…" : "Сохранить оценки"}
          </button>
        </div>

        {/* Elder + add resident */}
        <div className="space-y-5">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-3">
            <h3 className="font-semibold flex items-center gap-2"><Star className="h-4 w-4 text-amber-400" /> Староста блока</h3>
            <select
              data-testid="elder-select"
              value={elder}
              onChange={(e) => saveElder(e.target.value)}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm bg-white"
            >
              <option value="">— не назначен —</option>
              {residents.map((r) => (
                <option key={r.id} value={r.full_name}>{r.full_name}</option>
              ))}
            </select>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 space-y-3">
            <h3 className="font-semibold flex items-center gap-2"><UserPlus className="h-4 w-4 text-pink-400" /> Добавить проживающего</h3>
            <div className="flex gap-2">
              <input
                data-testid="new-resident-name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="ФИО"
                className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
              <input
                value={newRoom}
                onChange={(e) => setNewRoom(e.target.value)}
                placeholder="комн."
                className="w-20 rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
            <button onClick={addResident} className="w-full py-2 rounded-xl border border-pink-300 text-pink-600 font-medium hover:bg-pink-50">
              Добавить
            </button>
          </div>
        </div>
      </div>

      {/* History */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5">
        <h3 className="font-semibold mb-3">История проверок</h3>
        {inspections.length === 0 && <div className="text-sm text-muted-foreground">Пока нет проверок.</div>}
        <div className="space-y-2">
          {inspections.map((i) => (
            <div
              key={i.id}
              className={`flex items-center justify-between rounded-xl border px-4 py-2.5 ${
                i.problem ? "bg-red-50 border-red-300" : "bg-slate-50 border-slate-200"
              }`}
            >
              <div className="flex items-center gap-4">
                <span className="font-mono text-sm font-semibold w-24">{i.date}</span>
                <div className="flex gap-1.5">
                  {["small_room", "big_room", "common"].map((k) => (
                    <span key={k} className={`h-7 w-7 rounded-md border grid place-items-center text-xs font-bold ${gradeColor(i[k])}`}>
                      {i[k] || "—"}
                    </span>
                  ))}
                </div>
                {i.note && <span className="text-xs text-muted-foreground italic truncate max-w-[200px]">{i.note}</span>}
              </div>
              <div className="flex items-center gap-3">
                <span className="text-[11px] text-slate-400">{i.created_by}</span>
                <button onClick={() => del(i.id)} className="text-slate-400 hover:text-red-500">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
