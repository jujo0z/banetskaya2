import React, { useEffect, useMemo, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  FileSignature, Printer, Download, Upload, Plus, Copy, Trash2, Eraser, Save,
  Wand2, ChevronDown, PenSquare, Type, Minus, Bold, Italic, Underline,
  AlignLeft, AlignCenter, AlignRight, RotateCcw, CheckSquare, Square, Database, Columns2,
} from "lucide-react";
import {
  zayavlenieFields, getZayavlenieDefaults, saveZayavlenieDefaults, zayavleniePrefill,
  openZayavleniePdf, downloadZayavleniePdf, masterUpload, downloadMasterTemplate,
  getZayavlenieTemplate, saveZayavlenieTemplate, resetZayavlenieTemplate,
  getZayavlenieRecords, saveZayavlenieRecords, getCustomColumns,
} from "@/lib/apiClient";
import ZayavPreview from "@/components/ZayavPreview";
import { zayavOverlayText } from "@/lib/zayavOverlay";

const recordLabel = (r, i) => (r.fio && String(r.fio).trim()) || `Заявление ${i + 1}`;
const stripEmpty = (obj) => {
  const out = {};
  Object.entries(obj || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && String(v).trim() !== "") out[k] = v;
  });
  return out;
};
const uid = () => "u" + Math.random().toString(36).slice(2, 9);

export default function Zayavlenie() {
  const [groups, setGroups] = useState([]);
  const [defaults, setDefaults] = useState({});
  const [records, setRecords] = useState([{}]);
  const [activeIdx, setActiveIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showDefaults, setShowDefaults] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [savingDefaults, setSavingDefaults] = useState(false);

  // ---- шаблон (редактируемый бланк) ----
  const [template, setTemplate] = useState([]);
  const [slotsMeta, setSlotsMeta] = useState([]);
  const [page, setPage] = useState(1);
  const [editMode, setEditMode] = useState(false);
  const [twoUp, setTwoUp] = useState(false);
  const [flipEdge, setFlipEdge] = useState("long");
  const [selectedId, setSelectedId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [savingTpl, setSavingTpl] = useState(false);

  const location = useLocation();
  const fileRef = useRef(null);
  const loadedRef = useRef(false);
  const saveTimer = useRef(null);

  const pIdx = activeIdx >= 0 ? activeIdx : 0;
  const rec = records[pIdx] || {};
  const values = useMemo(() => zayavOverlayText(rec), [rec]);
  // Для предпросмотра «2 на лист»: пара, к которой относится активная запись
  const pairStart = pIdx - (pIdx % 2);
  const leftRec = records[pairStart] || {};
  const rightRec = records[pairStart + 1] || {};
  const leftVals = useMemo(() => zayavOverlayText(leftRec), [leftRec]);
  const rightVals = useMemo(() => zayavOverlayText(rightRec), [rightRec]);
  const pageElements = useMemo(() => template.filter((e) => Number(e.page) === page), [template, page]);
  const selectedEl = useMemo(() => template.find((e) => e.id === selectedId) || null, [template, selectedId]);
  const selectedCount = useMemo(() => records.filter((r) => r.__print !== false).length, [records]);

  useEffect(() => {
    (async () => {
      try {
        const [f, d, tpl, saved] = await Promise.all([
          zayavlenieFields(), getZayavlenieDefaults(), getZayavlenieTemplate(), getZayavlenieRecords(),
        ]);
        setGroups(f.groups || []);
        setDefaults(d || {});
        setTemplate((tpl.template || []).map((e) => ({ ...e, id: e.id || uid() })));
        let slots = tpl.slots || [];
        try {
          const cc = await getCustomColumns();
          const extra = (cc.columns || []).map((c) => ({ slot: c.key, label: `★ ${c.label}` }));
          slots = [...slots, ...extra];
        } catch (e) { /* нет своих столбцов — не критично */ }
        setSlotsMeta(slots);
        const prefillList = location.state?.prefillList || null;
        if (Array.isArray(prefillList) && prefillList.length) {
          const recs = await zayavleniePrefill(prefillList);
          setRecords(recs.map((r) => ({ ...(d || {}), ...r })));
          toast.success(`Подставлено заявлений: ${recs.length}`);
        } else if (Array.isArray(saved) && saved.length) {
          setRecords(saved);
          toast.success(`Загружено сохранённых заявлений: ${saved.length}`);
        } else {
          setRecords([{ ...(d || {}) }]);
        }
      } catch (e) {
        toast.error("Не удалось загрузить данные Заявления");
      } finally {
        setLoading(false);
        setTimeout(() => { loadedRef.current = true; }, 400);
      }
    })();
  }, []);

  // Авто-сохранение списка заявлений в БД («загрузить один раз»)
  useEffect(() => {
    if (!loadedRef.current) return;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      saveZayavlenieRecords(records).catch(() => {});
    }, 900);
    return () => { if (saveTimer.current) clearTimeout(saveTimer.current); };
  }, [records]);

  // ---- Excel / defaults / records (без изменений логики) ----
  const onUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const data = await masterUpload(file);
      const recs = data.zayavlenie || [];
      if (!recs.length) toast.error("В файле не найдено данных");
      else {
        setRecords(recs.map((r) => ({ ...defaults, ...r })));
        setActiveIdx(0);
        toast.success(`Загружено: ${recs.length}`);
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Ошибка загрузки Excel");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };
  const onDownloadTemplate = async () => {
    try { await downloadMasterTemplate(); toast.success("Шаблон Excel скачан"); }
    catch { toast.error("Не удалось скачать шаблон"); }
  };
  const setDefaultVal = (key, val) => setDefaults((d) => ({ ...d, [key]: val }));
  const applyDefaultsToAll = () => setRecords((rs) => rs.map((r) => ({ ...defaults, ...stripEmpty(r) })));
  const doSaveDefaults = async () => {
    setSavingDefaults(true);
    try { await saveZayavlenieDefaults(stripEmpty(defaults)); applyDefaultsToAll(); toast.success("Постоянные значения сохранены"); }
    catch { toast.error("Не удалось сохранить"); }
    finally { setSavingDefaults(false); }
  };
  const setRecordVal = (idx, key, val) => setRecords((rs) => rs.map((r, i) => (i === idx ? { ...r, [key]: val } : r)));
  const addRecord = () => setRecords((rs) => { const n = [...rs, { ...defaults }]; setActiveIdx(n.length - 1); return n; });
  const duplicateRecord = (idx) => setRecords((rs) => { const n = [...rs]; n.splice(idx + 1, 0, { ...rs[idx] }); setActiveIdx(idx + 1); return n; });
  const removeRecord = (idx) => setRecords((rs) => { if (rs.length <= 1) return [{ ...defaults }]; const n = rs.filter((_, i) => i !== idx); setActiveIdx((a) => Math.min(a, n.length - 1)); return n; });
  const clearRecordAt = (idx) => setRecords((rs) => rs.map((r, i) => (i === idx ? { ...defaults } : r)));

  const toggleSelect = (idx) => setRecords((rs) => rs.map((r, i) => (i === idx ? { ...r, __print: r.__print === false } : r)));
  const setAllSelected = (val) => setRecords((rs) => rs.map((r) => ({ ...r, __print: val })));
  const selectedRecords = () => records.filter((r) => r.__print !== false).map(({ __print, ...r }) => r);

  const doOpen = async () => {
    const sel = selectedRecords();
    if (!sel.length) { toast.error("Отметьте хотя бы одно заявление для печати"); return; }
    try { await openZayavleniePdf(sel, flipEdge, twoUp); toast(`PDF (${sel.length})${twoUp ? " · 2 на лист" : ""} открыт — печать в масштабе 100%`); }
    catch { toast.error("Ошибка открытия PDF"); }
  };
  const doDownload = async () => {
    const sel = selectedRecords();
    if (!sel.length) { toast.error("Отметьте хотя бы одно заявление"); return; }
    try { await downloadZayavleniePdf(sel, flipEdge, twoUp); } catch { toast.error("Ошибка скачивания"); }
  };

  // ---- Редактор шаблона ----
  const updateEl = (id, patch) => setTemplate((t) => t.map((e) => (e.id === id ? { ...e, ...patch } : e)));
  const deleteEl = (id) => { setTemplate((t) => t.filter((e) => e.id !== id)); setSelectedId(null); };
  const dupEl = (id) => setTemplate((t) => {
    const el = t.find((e) => e.id === id); if (!el) return t;
    const copy = { ...el, id: uid(), x: Math.min(96, (el.x || 0) + 2), y: Math.min(97, (el.y || 0) + 2) };
    setSelectedId(copy.id); return [...t, copy];
  });
  const addText = () => setTemplate((t) => {
    const el = { id: uid(), type: "text", page, x: 20, y: 20, align: "left", text: "Новый текст", size: 9, bold: false, italic: false, font: "serif", color: "#17171f" };
    setSelectedId(el.id); return [...t, el];
  });
  const addLine = () => setTemplate((t) => {
    const el = { id: uid(), type: "line", page, x: 10, y: 30, w: 60, thickness: 0.5, color: "#17171f" };
    setSelectedId(el.id); return [...t, el];
  });
  const addField = () => setTemplate((t) => {
    const firstSlot = (slotsMeta[0] && slotsMeta[0].slot) || "applicant";
    const el = { id: uid(), type: "field", field: firstSlot, page, x: 30, y: 30, align: "left", size: 9, bold: false, italic: false, underline: false, font: "serif", color: "#0a0d52", w: 0 };
    setSelectedId(el.id); return [...t, el];
  });
  const commitText = (id, text) => { updateEl(id, { text }); setEditingId(null); };
  const doSaveTpl = async () => {
    setSavingTpl(true);
    try { await saveZayavlenieTemplate(template.map(({ ...e }) => e)); toast.success("Шаблон сохранён"); }
    catch { toast.error("Не удалось сохранить шаблон"); }
    finally { setSavingTpl(false); }
  };
  const doResetTpl = async () => {
    if (!window.confirm("Сбросить бланк к оригинальному виду? Все правки шаблона будут удалены.")) return;
    setSavingTpl(true);
    try {
      const res = await resetZayavlenieTemplate();
      setTemplate((res.template || []).map((e) => ({ ...e, id: e.id || uid() })));
      setSelectedId(null); setEditingId(null);
      toast.success("Шаблон сброшен к оригиналу");
    } catch { toast.error("Не удалось сбросить"); }
    finally { setSavingTpl(false); }
  };

  if (loading) return <div className="p-8 text-muted-foreground">Загрузка…</div>;

  const isText = selectedEl && (selectedEl.type === "text" || selectedEl.type === "field");
  const isLine = selectedEl && selectedEl.type === "line";

  return (
    <div className="p-6 lg:p-8 space-y-6" data-testid="zayavlenie-page">
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight flex items-center gap-3">
          <FileSignature className="h-8 w-8 text-[#EC4899]" /> Заявление о регистрации
        </h1>
        <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
          «По месту пребывания», A4 (2 страницы). Весь бланк — <b>редактируемый шаблон</b>: включите
          «Редактор шаблона», чтобы менять надписи, двигать/добавлять/удалять текст, линии и
          <b> поля данных</b> (кнопка «Поле (данные)» — ячейка, которую программа сама заполнит).
          Кнопка <b>«2 на лист»</b> печатает 2 разных человека на одном листе A4 — оба из одного шаблона.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[400px_minmax(0,1fr)] gap-6">
        {/* ---- Left controls ---- */}
        <div className="space-y-4">
          {/* Excel */}
          <div className="rounded-lg border border-pink-100 bg-white/80 p-4 space-y-2">
            <div className="text-sm font-semibold flex items-center gap-2"><Upload className="h-4 w-4 text-[#EC4899]" /> Загрузка из Excel</div>
            <input ref={fileRef} type="file" accept=".xlsx,.xlsm" onChange={onUpload} className="hidden" data-testid="zayav-file-input" />
            <Button onClick={() => fileRef.current?.click()} disabled={uploading} variant="outline" className="w-full" data-testid="zayav-upload-btn">
              <Upload className="h-4 w-4 mr-2" />{uploading ? "Загрузка…" : "Выбрать .xlsx файл"}
            </Button>
            <Button onClick={onDownloadTemplate} variant="ghost" className="w-full text-[#EC4899] hover:text-[#EC4899]" data-testid="zayav-download-template-btn">
              <Download className="h-4 w-4 mr-2" />Скачать шаблон Excel
            </Button>
          </div>

          {/* Defaults */}
          <div className="rounded-lg border border-[#EC4899]/30 bg-[#EC4899]/5 p-4 space-y-2">
            <button type="button" onClick={() => setShowDefaults((s) => !s)} className="flex w-full items-center justify-between text-sm font-semibold" data-testid="zayav-defaults-toggle">
              <span className="flex items-center gap-2"><Wand2 className="h-4 w-4 text-[#EC4899]" /> Постоянные значения</span>
              <ChevronDown className={`h-4 w-4 transition-transform ${showDefaults ? "" : "-rotate-90"}`} />
            </button>
            {showDefaults && (
              <div className="space-y-3 pt-2 max-h-[360px] overflow-auto pr-1">
                {groups.map((g) => (
                  <div key={g.group}>
                    <div className="text-[10px] uppercase tracking-wider text-[#EC4899] font-semibold mb-1.5">{g.group}</div>
                    <div className="space-y-1.5">
                      {g.fields.map((f) => (
                        <div key={f.key}>
                          <Label className="text-[11px] text-muted-foreground">{f.label}</Label>
                          <Input value={defaults[f.key] || ""} onChange={(e) => setDefaultVal(f.key, e.target.value)} className="h-8 text-sm" data-testid={`zayav-default-${f.key}`} />
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <Button onClick={doSaveDefaults} disabled={savingDefaults} className="w-full bg-[#EC4899] hover:bg-[#DB2777]" data-testid="zayav-save-defaults">
              <Save className="h-4 w-4 mr-2" />{savingDefaults ? "…" : "Сохранить и применить"}
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <Button onClick={doOpen} className="bg-[#EC4899] hover:bg-[#DB2777]" data-testid="zayav-open"><Printer className="h-4 w-4 mr-2" /> Печать ({selectedCount})</Button>
            <Button onClick={doDownload} variant="outline" data-testid="zayav-download"><Download className="h-4 w-4 mr-2" /> Скачать ({selectedCount})</Button>
          </div>

          {/* Records */}
          <div className="rounded-lg border border-pink-100 bg-white/80 p-4 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <div className="text-sm font-semibold">Заявления ({records.length}) · выбрано {selectedCount}</div>
              <div className="flex items-center gap-1">
                <button type="button" onClick={() => setAllSelected(true)} className="text-[11px] px-1.5 py-1 rounded border border-pink-100 hover:bg-white flex items-center gap-1" title="Выбрать все" data-testid="zayav-select-all"><CheckSquare className="h-3.5 w-3.5" /> Все</button>
                <button type="button" onClick={() => setAllSelected(false)} className="text-[11px] px-1.5 py-1 rounded border border-pink-100 hover:bg-white flex items-center gap-1" title="Снять выбор" data-testid="zayav-select-none"><Square className="h-3.5 w-3.5" /> Снять</button>
                <Button size="sm" variant="outline" onClick={addRecord} data-testid="zayav-add-record"><Plus className="h-4 w-4 mr-1" /> Добавить</Button>
              </div>
            </div>
            <p className="text-[11px] text-muted-foreground">Отметьте галочками, какие заявления печатать. Список сохраняется автоматически — грузить Excel заново не нужно.</p>
            <div className="space-y-2 max-h-[460px] overflow-auto pr-1">
              {records.map((r, idx) => {
                const open = idx === activeIdx;
                const checked = r.__print !== false;
                return (
                  <div key={idx} className={`rounded-md border ${checked ? "border-[#EC4899]/40" : "border-pink-100"} bg-white/60`} data-testid={`zayav-record-${idx}`}>
                    <div className="flex items-center gap-1 px-2 py-1.5">
                      <input type="checkbox" checked={checked} onChange={() => toggleSelect(idx)} className="h-4 w-4 accent-[#EC4899] cursor-pointer" title="Печатать это заявление" data-testid={`zayav-record-check-${idx}`} />
                      <button type="button" onClick={() => setActiveIdx(open ? -1 : idx)} className="flex items-center gap-2 flex-1 min-w-0 text-left text-sm" data-testid={`zayav-record-toggle-${idx}`}>
                        <ChevronDown className={`h-4 w-4 shrink-0 transition-transform ${open ? "" : "-rotate-90"}`} />
                        <span className="truncate">{recordLabel(r, idx)}</span>
                      </button>
                      <button type="button" title="Дублировать" onClick={() => duplicateRecord(idx)} className="p-1.5 text-muted-foreground hover:text-slate-900"><Copy className="h-3.5 w-3.5" /></button>
                      <button type="button" title="Очистить" onClick={() => clearRecordAt(idx)} className="p-1.5 text-muted-foreground hover:text-slate-900"><Eraser className="h-3.5 w-3.5" /></button>
                      <button type="button" title="Удалить" onClick={() => removeRecord(idx)} className="p-1.5 text-muted-foreground hover:text-[#EC4899]" data-testid={`zayav-record-del-${idx}`}><Trash2 className="h-3.5 w-3.5" /></button>
                    </div>
                    {open && (
                      <div className="px-3 pb-3 pt-1 space-y-3 border-t border-pink-100">
                        {groups.map((g) => (
                          <div key={g.group}>
                            <div className="text-[10px] uppercase tracking-wider text-[#EC4899] font-semibold mb-1.5">{g.group}</div>
                            <div className="space-y-1.5">
                              {g.fields.map((f) => (
                                <div key={f.key}>
                                  <Label className="text-[11px] text-muted-foreground">{f.label}</Label>
                                  <Input value={r[f.key] || ""} onChange={(e) => setRecordVal(idx, f.key, e.target.value)} className="h-8 text-sm" data-testid={`zayav-input-${idx}-${f.key}`} />
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* (старый левый редактор отключён — используется верхняя лента-тулбар) */}
          {false && (
            <div className="rounded-lg border border-amber-400/40 bg-amber-400/5 p-4 space-y-3" data-testid="zayav-tpl-editor">
              <div className="text-sm font-semibold flex items-center gap-2 text-amber-300"><PenSquare className="h-4 w-4" /> Редактор шаблона — стр. {page}</div>
              <div className="grid grid-cols-2 gap-2">
                <Button size="sm" variant="outline" onClick={addText} data-testid="zayav-add-text"><Type className="h-4 w-4 mr-1" /> Текст</Button>
                <Button size="sm" variant="outline" onClick={addLine} data-testid="zayav-add-line"><Minus className="h-4 w-4 mr-1" /> Линия</Button>
              </div>
              <p className="text-[11px] text-muted-foreground">Клик — выбрать, тащить — двигать, 2× клик по тексту — редактировать надпись.</p>

              {selectedEl ? (
                <div className="space-y-2 border-t border-pink-100 pt-2">
                  <div className="text-[12px] font-semibold text-slate-800 flex items-center justify-between">
                    <span>{selectedEl.type === "field" ? `Поле: ${selectedEl.field}` : selectedEl.type === "line" ? "Линия" : "Текст"}</span>
                    <span className="flex gap-1">
                      <button title="Дублировать" onClick={() => dupEl(selectedEl.id)} className="p-1 text-muted-foreground hover:text-slate-900"><Copy className="h-3.5 w-3.5" /></button>
                      <button title="Удалить" onClick={() => deleteEl(selectedEl.id)} className="p-1 text-muted-foreground hover:text-[#EC4899]" data-testid="zayav-el-delete"><Trash2 className="h-3.5 w-3.5" /></button>
                    </span>
                  </div>

                  {selectedEl.type === "text" && (
                    <div>
                      <Label className="text-[10px] text-muted-foreground">Текст надписи</Label>
                      <Input value={selectedEl.text || ""} onChange={(e) => updateEl(selectedEl.id, { text: e.target.value })} className="h-8 text-sm" data-testid="zayav-el-text" />
                    </div>
                  )}
                  {selectedEl.type === "field" && (
                    <div>
                      <Label className="text-[10px] text-muted-foreground">Какое поле данных</Label>
                      <select value={selectedEl.field} onChange={(e) => updateEl(selectedEl.id, { field: e.target.value })} className="h-8 w-full rounded-md bg-white/70 border border-pink-100 text-sm px-2" data-testid="zayav-el-field">
                        {slotsMeta.map((s) => (<option key={s.slot} value={s.slot}>{s.label}</option>))}
                      </select>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-2">
                    <div><Label className="text-[10px] text-muted-foreground">X, %</Label>
                      <Input type="number" step="0.1" value={selectedEl.x ?? ""} onChange={(e) => updateEl(selectedEl.id, { x: parseFloat(e.target.value) })} className="h-8 text-sm" data-testid="zayav-el-x" /></div>
                    <div><Label className="text-[10px] text-muted-foreground">Y, %</Label>
                      <Input type="number" step="0.1" value={selectedEl.y ?? ""} onChange={(e) => updateEl(selectedEl.id, { y: parseFloat(e.target.value) })} className="h-8 text-sm" data-testid="zayav-el-y" /></div>
                  </div>

                  {isText && (
                    <>
                      <div className="grid grid-cols-2 gap-2">
                        <div><Label className="text-[10px] text-muted-foreground">Кегль (pt)</Label>
                          <Input type="number" step="0.1" value={selectedEl.size ?? ""} onChange={(e) => updateEl(selectedEl.id, { size: parseFloat(e.target.value) })} className="h-8 text-sm" data-testid="zayav-el-size" /></div>
                        <div><Label className="text-[10px] text-muted-foreground">Макс. ширина, % (0 = авто)</Label>
                          <Input type="number" step="0.5" value={selectedEl.w ?? 0} onChange={(e) => updateEl(selectedEl.id, { w: parseFloat(e.target.value) })} className="h-8 text-sm" /></div>
                      </div>
                      <div className="flex items-center gap-1 flex-wrap">
                        <button title="Жирный" onClick={() => updateEl(selectedEl.id, { bold: !selectedEl.bold })} className={`p-1.5 rounded border border-pink-100 ${selectedEl.bold ? "bg-white" : ""}`} data-testid="zayav-el-bold"><Bold className="h-3.5 w-3.5" /></button>
                        <button title="Курсив" onClick={() => updateEl(selectedEl.id, { italic: !selectedEl.italic })} className={`p-1.5 rounded border border-pink-100 ${selectedEl.italic ? "bg-white" : ""}`}><Italic className="h-3.5 w-3.5" /></button>
                        <span className="w-px h-5 bg-white mx-1" />
                        {[["left", AlignLeft], ["center", AlignCenter], ["right", AlignRight]].map(([a, Ic]) => (
                          <button key={a} title={a} onClick={() => updateEl(selectedEl.id, { align: a })} className={`p-1.5 rounded border border-pink-100 ${selectedEl.align === a ? "bg-white" : ""}`}><Ic className="h-3.5 w-3.5" /></button>
                        ))}
                        <span className="w-px h-5 bg-white mx-1" />
                        <select value={selectedEl.font || "serif"} onChange={(e) => updateEl(selectedEl.id, { font: e.target.value })} className="h-7 rounded bg-white/70 border border-pink-100 text-xs px-1">
                          <option value="serif">Times</option>
                          <option value="sans">Arial</option>
                        </select>
                        <input type="color" value={selectedEl.color || "#17171f"} onChange={(e) => updateEl(selectedEl.id, { color: e.target.value })} className="h-7 w-8 rounded border border-pink-100 bg-transparent" title="Цвет" />
                      </div>
                    </>
                  )}
                  {isLine && (
                    <div className="grid grid-cols-2 gap-2">
                      <div><Label className="text-[10px] text-muted-foreground">Длина, %</Label>
                        <Input type="number" step="0.5" value={selectedEl.w ?? ""} onChange={(e) => updateEl(selectedEl.id, { w: parseFloat(e.target.value) })} className="h-8 text-sm" /></div>
                      <div><Label className="text-[10px] text-muted-foreground">Толщина (pt)</Label>
                        <Input type="number" step="0.1" value={selectedEl.thickness ?? ""} onChange={(e) => updateEl(selectedEl.id, { thickness: parseFloat(e.target.value) })} className="h-8 text-sm" /></div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-[12px] text-muted-foreground border-t border-pink-100 pt-2">Выберите элемент в бланке или добавьте новый.</div>
              )}

              <div className="grid grid-cols-2 gap-2 pt-1 border-t border-pink-100">
                <Button onClick={doSaveTpl} disabled={savingTpl} className="bg-amber-500 hover:bg-amber-600 text-black" data-testid="zayav-save-tpl"><Save className="h-4 w-4 mr-1" /> {savingTpl ? "…" : "Сохранить шаблон"}</Button>
                <Button onClick={doResetTpl} disabled={savingTpl} variant="outline" data-testid="zayav-reset-tpl"><RotateCcw className="h-4 w-4 mr-1" /> Сбросить</Button>
              </div>
            </div>
          )}
        </div>

        {/* ---- Preview ---- */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-muted-foreground">Предпросмотр — {page === 2 ? "страница 2 (оборот)" : "страница 1 (лицо)"}</div>
            <div className="flex items-center gap-2">
              <div className="flex rounded-md border border-pink-100 overflow-hidden">
                <button type="button" onClick={() => setPage(1)} className={`px-3 py-1.5 text-xs transition ${page === 1 ? "bg-[#EC4899] text-white font-semibold" : "text-muted-foreground hover:text-slate-900"}`} data-testid="zayav-page-1-btn">Стр. 1</button>
                <button type="button" onClick={() => setPage(2)} className={`px-3 py-1.5 text-xs transition ${page === 2 ? "bg-[#EC4899] text-white font-semibold" : "text-muted-foreground hover:text-slate-900"}`} data-testid="zayav-page-2-btn">Стр. 2</button>
              </div>
              <Button size="sm" variant={twoUp ? "default" : "ghost"} onClick={() => setTwoUp((v) => !v)} className={twoUp ? "bg-[#2563eb] hover:bg-[#1d4ed8] text-white" : ""} title="Печатать по 2 разных человека на одном листе A4 (альбомный)" data-testid="zayav-toggle-2up">
                <Columns2 className="h-4 w-4 mr-1" /> {twoUp ? "2 на лист ✓" : "1 на лист"}
              </Button>
              {twoUp && (
                <select value={flipEdge} onChange={(e) => setFlipEdge(e.target.value)} className="h-8 rounded-md bg-white/70 border border-pink-100 text-xs px-2" title="Как принтер переворачивает лист при двусторонней печати. Если оборот встал перевёрнутым — смените вариант" data-testid="zayav-flip-edge">
                  <option value="long">Оборот: длинный край</option>
                  <option value="short">Оборот: короткий край</option>
                </select>
              )}
              <Button size="sm" variant={editMode ? "default" : "ghost"} onClick={() => { setEditMode((v) => !v); setSelectedId(null); setEditingId(null); }} className={editMode ? "bg-amber-500 hover:bg-amber-600 text-black" : ""} data-testid="zayav-toggle-edit">
                <PenSquare className="h-4 w-4 mr-1" /> {editMode ? "Готово" : "Редактор шаблона"}
              </Button>
            </div>
          </div>
          {editMode && (
            <div className="rounded-md border border-amber-400/40 bg-[#FDECF5] px-2 py-1.5 mb-2 flex flex-wrap items-center gap-1.5 sticky top-0 z-20" data-testid="zayav-ribbon">
              <button onClick={addText} title="Добавить текст" className="flex items-center gap-1 h-7 px-2 rounded border border-pink-100 text-xs hover:bg-white" data-testid="zayav-add-text"><Type className="h-3.5 w-3.5" /> Текст</button>
              <button onClick={addLine} title="Добавить линию" className="flex items-center gap-1 h-7 px-2 rounded border border-pink-100 text-xs hover:bg-white" data-testid="zayav-add-line"><Minus className="h-3.5 w-3.5" /> Линия</button>
              <button onClick={addField} title="Добавить ячейку, которую программа заполнит из данных" className="flex items-center gap-1 h-7 px-2 rounded border border-[#2563eb]/50 bg-[#2563eb]/15 text-[#93c5fd] text-xs hover:bg-[#2563eb]/25" data-testid="zayav-add-field"><Database className="h-3.5 w-3.5" /> Поле (данные)</button>
              <span className="w-px h-6 bg-white/15 mx-1" />
              {!selectedEl && <span className="text-[11px] text-muted-foreground">Выберите элемент в бланке…</span>}
              {isText && (
                <>
                  <select value={selectedEl.font || "serif"} onChange={(e) => updateEl(selectedEl.id, { font: e.target.value })} className="h-7 rounded bg-white/70 border border-pink-100 text-xs px-1" data-testid="zayav-rb-font" title="Шрифт">
                    <option value="serif">Times New Roman</option>
                    <option value="sans">Arial</option>
                  </select>
                  <div className="flex items-center h-7 rounded border border-pink-100 overflow-hidden">
                    <button onClick={() => updateEl(selectedEl.id, { size: Math.max(4, +((selectedEl.size || 9) - 0.5).toFixed(1)) })} className="px-1.5 hover:bg-white text-sm">−</button>
                    <input type="number" step="0.1" value={selectedEl.size ?? ""} onChange={(e) => updateEl(selectedEl.id, { size: parseFloat(e.target.value) })} className="w-12 h-full bg-white/70 text-center text-xs outline-none" data-testid="zayav-rb-size" />
                    <button onClick={() => updateEl(selectedEl.id, { size: +((selectedEl.size || 9) + 0.5).toFixed(1) })} className="px-1.5 hover:bg-white text-sm">+</button>
                  </div>
                  <button onClick={() => updateEl(selectedEl.id, { bold: !selectedEl.bold })} className={`h-7 w-7 grid place-items-center rounded border border-pink-100 ${selectedEl.bold ? "bg-white/25" : "hover:bg-white"}`} data-testid="zayav-rb-bold"><Bold className="h-3.5 w-3.5" /></button>
                  <button onClick={() => updateEl(selectedEl.id, { italic: !selectedEl.italic })} className={`h-7 w-7 grid place-items-center rounded border border-pink-100 ${selectedEl.italic ? "bg-white/25" : "hover:bg-white"}`} data-testid="zayav-rb-italic"><Italic className="h-3.5 w-3.5" /></button>
                  <button onClick={() => updateEl(selectedEl.id, { underline: !selectedEl.underline })} className={`h-7 w-7 grid place-items-center rounded border border-pink-100 ${selectedEl.underline ? "bg-white/25" : "hover:bg-white"}`} data-testid="zayav-rb-underline"><Underline className="h-3.5 w-3.5" /></button>
                  <span className="w-px h-6 bg-white/15 mx-0.5" />
                  {[["left", AlignLeft], ["center", AlignCenter], ["right", AlignRight]].map(([a, Ic]) => (
                    <button key={a} onClick={() => updateEl(selectedEl.id, { align: a })} className={`h-7 w-7 grid place-items-center rounded border border-pink-100 ${selectedEl.align === a ? "bg-white/25" : "hover:bg-white"}`} data-testid={`zayav-rb-align-${a}`}><Ic className="h-3.5 w-3.5" /></button>
                  ))}
                  <input type="color" value={selectedEl.color || "#17171f"} onChange={(e) => updateEl(selectedEl.id, { color: e.target.value })} className="h-7 w-8 rounded border border-pink-100 bg-transparent p-0.5" title="Цвет" data-testid="zayav-rb-color" />
                  {selectedEl.type === "field" && (
                    <select value={selectedEl.field} onChange={(e) => updateEl(selectedEl.id, { field: e.target.value })} className="h-7 rounded bg-white/70 border border-pink-100 text-xs px-1 max-w-[160px]" data-testid="zayav-rb-field" title="Поле данных">
                      {slotsMeta.map((s) => (<option key={s.slot} value={s.slot}>{s.label}</option>))}
                    </select>
                  )}
                </>
              )}
              {isLine && (
                <>
                  <span className="text-[11px] text-muted-foreground">Линия:</span>
                  <label className="text-[11px] text-muted-foreground">длина</label>
                  <input type="number" step="0.5" value={selectedEl.w ?? ""} onChange={(e) => updateEl(selectedEl.id, { w: parseFloat(e.target.value) })} className="w-16 h-7 bg-white/70 border border-pink-100 rounded text-center text-xs" />
                  <label className="text-[11px] text-muted-foreground">толщина</label>
                  <input type="number" step="0.1" value={selectedEl.thickness ?? ""} onChange={(e) => updateEl(selectedEl.id, { thickness: parseFloat(e.target.value) })} className="w-14 h-7 bg-white/70 border border-pink-100 rounded text-center text-xs" />
                  <input type="color" value={selectedEl.color || "#17171f"} onChange={(e) => updateEl(selectedEl.id, { color: e.target.value })} className="h-7 w-8 rounded border border-pink-100 bg-transparent p-0.5" title="Цвет" />
                </>
              )}
              {selectedEl && (
                <>
                  <span className="w-px h-6 bg-white/15 mx-1" />
                  <button onClick={() => dupEl(selectedEl.id)} title="Дублировать" className="h-7 w-7 grid place-items-center rounded border border-pink-100 hover:bg-white"><Copy className="h-3.5 w-3.5" /></button>
                  <button onClick={() => deleteEl(selectedEl.id)} title="Удалить" className="h-7 w-7 grid place-items-center rounded border border-pink-100 hover:bg-[#EC4899]/30" data-testid="zayav-el-delete"><Trash2 className="h-3.5 w-3.5" /></button>
                </>
              )}
              <span className="flex-1" />
              <button onClick={doSaveTpl} disabled={savingTpl} className="flex items-center gap-1 h-7 px-2 rounded bg-amber-500 hover:bg-amber-600 text-black text-xs font-semibold" data-testid="zayav-save-tpl"><Save className="h-3.5 w-3.5" /> Сохранить</button>
              <button onClick={doResetTpl} disabled={savingTpl} className="flex items-center gap-1 h-7 px-2 rounded border border-pink-100 text-xs hover:bg-white" data-testid="zayav-reset-tpl"><RotateCcw className="h-3.5 w-3.5" /> Сбросить</button>
            </div>
          )}
          <div className="rounded-lg border border-pink-100 bg-white/80 p-3 shadow-2xl overflow-auto" style={{ maxHeight: "84vh" }}>
            {twoUp && !editMode ? (
              <div className="mx-auto" style={{ maxWidth: 980 }} data-testid="zayav-2up-preview">
                <div className="text-[11px] text-muted-foreground mb-1.5 text-center">Лист A4 (альбомный) — 2 разных человека. Разрезать по пунктиру.</div>
                <div className="flex ring-1 ring-black/10" style={{ aspectRatio: "297 / 210", background: "#fff" }}>
                  <div style={{ width: "50%", borderRight: "1px dashed #b9b9c2" }}>
                    <ZayavPreview page={page} elements={pageElements} values={leftVals} />
                  </div>
                  <div style={{ width: "50%" }}>
                    <ZayavPreview page={page} elements={pageElements} values={rightVals} />
                  </div>
                </div>
              </div>
            ) : (
              <div className="mx-auto ring-1 ring-black/10" style={{ maxWidth: 720 }}>
                <ZayavPreview
                  page={page}
                  elements={pageElements}
                  values={values}
                  editMode={editMode}
                  selectedId={selectedId}
                  editingId={editingId}
                  onSelect={setSelectedId}
                  onStartTextEdit={setEditingId}
                  onCommitText={commitText}
                  onChange={updateEl}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
