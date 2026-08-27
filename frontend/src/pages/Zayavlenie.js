import React, { useEffect, useMemo, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  FileSignature,
  Printer,
  Download,
  Upload,
  Plus,
  Copy,
  Trash2,
  Eraser,
  Save,
  Wand2,
  ChevronDown,
  SlidersHorizontal,
} from "lucide-react";
import {
  zayavlenieFields,
  getZayavlenieDefaults,
  saveZayavlenieDefaults,
  zayavleniePrefill,
  openZayavleniePdf,
  downloadZayavleniePdf,
  masterUpload,
  downloadMasterTemplate,
  getZayavlenieLayout,
  saveZayavlenieLayout,
  zayavlenieBackgroundUrl,
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

// «Заявление о регистрации по месту пребывания». Отрисовка: чистый бланк-фон
// (A4-портрет, 2 страницы) + слой данных по координатам (проценты страницы).
// Preview и PDF используют одну систему координат. Есть режим «Настройка полей».
export default function Zayavlenie() {
  const [groups, setGroups] = useState([]);
  const [defaults, setDefaults] = useState({});
  const [records, setRecords] = useState([{}]);
  const [activeIdx, setActiveIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showDefaults, setShowDefaults] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [savingDefaults, setSavingDefaults] = useState(false);

  // раскладка (координаты слотов) + режим настройки
  const [layout, setLayout] = useState(null);      // {"1":{slot:cfg}, "2":{...}}
  const [slotsMeta, setSlotsMeta] = useState([]);   // [{slot,page,label}]
  const [page, setPage] = useState(1);              // 1 | 2
  const [editMode, setEditMode] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [savingLayout, setSavingLayout] = useState(false);

  const location = useLocation();
  const fileRef = useRef(null);

  const rec = records[activeIdx] || {};
  const values = useMemo(() => zayavOverlayText(rec), [rec]);

  // слоты текущей страницы + подмешанные подписи (label) для редактора/плейсхолдеров
  const curSlots = useMemo(() => {
    const src = (layout && layout[String(page)]) || {};
    const meta = {};
    (slotsMeta || []).forEach((s) => (meta[s.slot] = s.label));
    const out = {};
    Object.entries(src).forEach(([k, cfg]) => {
      out[k] = { ...cfg, label: meta[k] || k };
    });
    return out;
  }, [layout, page, slotsMeta]);

  useEffect(() => {
    (async () => {
      try {
        const [f, d, lay] = await Promise.all([
          zayavlenieFields(),
          getZayavlenieDefaults(),
          getZayavlenieLayout(),
        ]);
        setGroups(f.groups || []);
        setDefaults(d || {});
        setLayout(lay.layout || { 1: {}, 2: {} });
        setSlotsMeta(lay.slots || []);
        const prefillList = location.state?.prefillList || null;
        if (Array.isArray(prefillList) && prefillList.length) {
          const recs = await zayavleniePrefill(prefillList);
          setRecords(recs.map((r) => ({ ...(d || {}), ...r })));
          toast.success(`Подставлено заявлений: ${recs.length}`);
        } else {
          setRecords([{ ...(d || {}) }]);
        }
      } catch (e) {
        toast.error("Не удалось загрузить данные Заявления");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const onUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const data = await masterUpload(file);
      const recs = data.zayavlenie || [];
      if (!recs.length) {
        toast.error("В файле не найдено данных");
      } else {
        setRecords(recs.map((r) => ({ ...defaults, ...r })));
        setActiveIdx(0);
        toast.success(`Загружено: ${recs.length} — данные подставлены`);
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Ошибка загрузки Excel");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const onDownloadTemplate = async () => {
    try {
      await downloadMasterTemplate();
      toast.success("Шаблон Excel скачан");
    } catch {
      toast.error("Не удалось скачать шаблон");
    }
  };

  const setDefaultVal = (key, val) => setDefaults((d) => ({ ...d, [key]: val }));
  const applyDefaultsToAll = () =>
    setRecords((rs) => rs.map((r) => ({ ...defaults, ...stripEmpty(r) })));
  const doSaveDefaults = async () => {
    setSavingDefaults(true);
    try {
      await saveZayavlenieDefaults(stripEmpty(defaults));
      applyDefaultsToAll();
      toast.success("Постоянные значения сохранены и применены");
    } catch (e) {
      toast.error("Не удалось сохранить");
    } finally {
      setSavingDefaults(false);
    }
  };

  const setRecordVal = (idx, key, val) =>
    setRecords((rs) => rs.map((r, i) => (i === idx ? { ...r, [key]: val } : r)));
  const addRecord = () =>
    setRecords((rs) => {
      const next = [...rs, { ...defaults }];
      setActiveIdx(next.length - 1);
      return next;
    });
  const duplicateRecord = (idx) =>
    setRecords((rs) => {
      const next = [...rs];
      next.splice(idx + 1, 0, { ...rs[idx] });
      setActiveIdx(idx + 1);
      return next;
    });
  const removeRecord = (idx) =>
    setRecords((rs) => {
      if (rs.length <= 1) return [{ ...defaults }];
      const next = rs.filter((_, i) => i !== idx);
      setActiveIdx((a) => Math.min(a, next.length - 1));
      return next;
    });
  const clearRecordAt = (idx) =>
    setRecords((rs) => rs.map((r, i) => (i === idx ? { ...defaults } : r)));

  const doOpen = async () => {
    try {
      await openZayavleniePdf(records);
      toast("PDF открыт — печатайте «Фактический размер» (100%)");
    } catch (e) {
      toast.error("Ошибка открытия PDF");
    }
  };
  const doDownload = async () => {
    try {
      await downloadZayavleniePdf(records);
    } catch (e) {
      toast.error("Ошибка скачивания");
    }
  };

  // ---- Редактор координат ----
  const patchSlot = (slot, patch) =>
    setLayout((L) => {
      const p = String(page);
      const cur = (L && L[p] && L[p][slot]) || {};
      return { ...L, [p]: { ...(L[p] || {}), [slot]: { ...cur, ...patch } } };
    });
  const doSaveLayout = async () => {
    setSavingLayout(true);
    try {
      await saveZayavlenieLayout(layout);
      toast.success("Раскладка полей сохранена");
    } catch (e) {
      toast.error("Не удалось сохранить раскладку");
    } finally {
      setSavingLayout(false);
    }
  };
  const doResetLayout = async () => {
    setSavingLayout(true);
    try {
      const res = await saveZayavlenieLayout({});
      setLayout(res.layout || { 1: {}, 2: {} });
      toast.success("Раскладка сброшена к стандартной");
    } catch (e) {
      toast.error("Не удалось сбросить");
    } finally {
      setSavingLayout(false);
    }
  };

  const selCfg = selectedSlot ? curSlots[selectedSlot] : null;

  if (loading) {
    return <div className="p-8 text-muted-foreground">Загрузка…</div>;
  }

  return (
    <div className="p-6 lg:p-8 space-y-6" data-testid="zayavlenie-page">
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight flex items-center gap-3">
          <FileSignature className="h-8 w-8 text-[#E11D48]" /> Заявление о регистрации
        </h1>
        <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
          «Заявление о регистрации по месту пребывания» на чистой бумаге A4 (2 страницы на человека).
          Данные накладываются поверх официального бланка. Печатайте <b>двусторонне</b> (стр. 1 — лицо,
          стр. 2 — оборот). Страница 2 частично заполняется от руки (площадь и число проживающих подставляются).
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[400px_minmax(0,1fr)] gap-6">
        {/* ---- Controls ---- */}
        <div className="space-y-4">
          {/* Excel upload */}
          <div className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-2">
            <div className="text-sm font-semibold flex items-center gap-2">
              <Upload className="h-4 w-4 text-[#E11D48]" /> Загрузка из Excel
            </div>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.xlsm"
              onChange={onUpload}
              className="hidden"
              data-testid="zayav-file-input"
            />
            <Button
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              variant="outline"
              className="w-full"
              data-testid="zayav-upload-btn"
            >
              <Upload className="h-4 w-4 mr-2" />
              {uploading ? "Загрузка…" : "Выбрать .xlsx файл"}
            </Button>
            <Button
              onClick={onDownloadTemplate}
              variant="ghost"
              className="w-full text-[#E11D48] hover:text-[#E11D48]"
              data-testid="zayav-download-template-btn"
            >
              <Download className="h-4 w-4 mr-2" />
              Скачать шаблон Excel
            </Button>
            <p className="text-[11px] text-muted-foreground">
              Единый шаблон «Данные»: одна строка = один человек. Заявитель, паспорт, адрес и дата
              подставляются автоматически.
            </p>
          </div>

          {/* Постоянные значения */}
          <div className="rounded-lg border border-[#E11D48]/30 bg-[#E11D48]/5 p-4 space-y-2" data-testid="zayav-defaults-box">
            <button
              type="button"
              onClick={() => setShowDefaults((s) => !s)}
              className="flex w-full items-center justify-between text-sm font-semibold"
              data-testid="zayav-defaults-toggle"
            >
              <span className="flex items-center gap-2">
                <Wand2 className="h-4 w-4 text-[#E11D48]" /> Постоянные значения
              </span>
              <ChevronDown className={`h-4 w-4 transition-transform ${showDefaults ? "" : "-rotate-90"}`} />
            </button>
            <p className="text-[11px] text-muted-foreground">
              Задайте один раз (площадь, адрес общежития и т.п.) — подставятся во все заявления.
              Данные из Excel имеют приоритет.
            </p>
            {showDefaults && (
              <div className="space-y-3 pt-2 max-h-[420px] overflow-auto pr-1">
                {groups.map((g) => (
                  <div key={g.group}>
                    <div className="text-[10px] uppercase tracking-wider text-[#E11D48] font-semibold mb-1.5">
                      {g.group}
                    </div>
                    <div className="space-y-1.5">
                      {g.fields.map((f) => (
                        <div key={f.key}>
                          <Label className="text-[11px] text-muted-foreground">{f.label}</Label>
                          <Input
                            value={defaults[f.key] || ""}
                            onChange={(e) => setDefaultVal(f.key, e.target.value)}
                            className="h-8 text-sm"
                            data-testid={`zayav-default-${f.key}`}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
            <Button
              onClick={doSaveDefaults}
              disabled={savingDefaults}
              className="w-full bg-[#E11D48] hover:bg-[#BE123C]"
              data-testid="zayav-save-defaults"
            >
              <Save className="h-4 w-4 mr-2" />
              {savingDefaults ? "Сохранение…" : "Сохранить и применить ко всем"}
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <Button onClick={doOpen} className="bg-[#E11D48] hover:bg-[#BE123C]" data-testid="zayav-open">
              <Printer className="h-4 w-4 mr-2" /> Открыть/Печать
            </Button>
            <Button onClick={doDownload} variant="outline" data-testid="zayav-download">
              <Download className="h-4 w-4 mr-2" /> Скачать PDF
            </Button>
          </div>

          {/* Records manager */}
          <div className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold">Заявления ({records.length})</div>
              <Button size="sm" variant="outline" onClick={addRecord} data-testid="zayav-add-record">
                <Plus className="h-4 w-4 mr-1" /> Добавить
              </Button>
            </div>
            <div className="space-y-2 max-h-[520px] overflow-auto pr-1">
              {records.map((r, idx) => {
                const open = idx === activeIdx;
                return (
                  <div key={idx} className="rounded-md border border-white/10 bg-black/20" data-testid={`zayav-record-${idx}`}>
                    <div className="flex items-center gap-1 px-2 py-1.5">
                      <button
                        type="button"
                        onClick={() => setActiveIdx(open ? -1 : idx)}
                        className="flex items-center gap-2 flex-1 min-w-0 text-left text-sm"
                        data-testid={`zayav-record-toggle-${idx}`}
                      >
                        <ChevronDown className={`h-4 w-4 shrink-0 transition-transform ${open ? "" : "-rotate-90"}`} />
                        <span className="truncate">{recordLabel(r, idx)}</span>
                      </button>
                      <button type="button" title="Дублировать" onClick={() => duplicateRecord(idx)} className="p-1.5 text-muted-foreground hover:text-white" data-testid={`zayav-record-dup-${idx}`}>
                        <Copy className="h-3.5 w-3.5" />
                      </button>
                      <button type="button" title="Очистить" onClick={() => clearRecordAt(idx)} className="p-1.5 text-muted-foreground hover:text-white">
                        <Eraser className="h-3.5 w-3.5" />
                      </button>
                      <button type="button" title="Удалить" onClick={() => removeRecord(idx)} className="p-1.5 text-muted-foreground hover:text-[#E11D48]" data-testid={`zayav-record-del-${idx}`}>
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    {open && (
                      <div className="px-3 pb-3 pt-1 space-y-3 border-t border-white/10">
                        {groups.map((g) => (
                          <div key={g.group}>
                            <div className="text-[10px] uppercase tracking-wider text-[#E11D48] font-semibold mb-1.5">{g.group}</div>
                            <div className="space-y-1.5">
                              {g.fields.map((f) => (
                                <div key={f.key}>
                                  <Label className="text-[11px] text-muted-foreground">{f.label}</Label>
                                  <Input
                                    value={r[f.key] || ""}
                                    onChange={(e) => setRecordVal(idx, f.key, e.target.value)}
                                    className="h-8 text-sm"
                                    data-testid={`zayav-input-${idx}-${f.key}`}
                                  />
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

          {/* Настройка полей (редактор координат) */}
          {editMode && (
            <div className="rounded-lg border border-amber-400/40 bg-amber-400/5 p-4 space-y-3" data-testid="zayav-field-editor">
              <div className="text-sm font-semibold flex items-center gap-2 text-amber-300">
                <SlidersHorizontal className="h-4 w-4" /> Настройка полей — стр. {page}
              </div>
              <p className="text-[11px] text-muted-foreground">
                Кликните поле в предпросмотре и перетащите мышью, либо задайте координаты числами.
                Значения в % от страницы. Работает и для preview, и для PDF.
              </p>
              {selCfg ? (
                <div className="space-y-2">
                  <div className="text-[12px] font-semibold text-white">{selCfg.label || selectedSlot}</div>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      ["x", "X, %"],
                      ["y", "Y, %"],
                      ["w", "Ширина, %"],
                      ["size", "Кегль (pt A4)"],
                    ].map(([k, lbl]) => (
                      <div key={k}>
                        <Label className="text-[10px] text-muted-foreground">{lbl}</Label>
                        <Input
                          type="number"
                          step="0.1"
                          value={selCfg[k] ?? ""}
                          onChange={(e) => patchSlot(selectedSlot, { [k]: parseFloat(e.target.value) })}
                          className="h-8 text-sm"
                          data-testid={`zayav-edit-${k}`}
                        />
                      </div>
                    ))}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1">
                      <Label className="text-[10px] text-muted-foreground">Выравнивание</Label>
                      <select
                        value={selCfg.align || "left"}
                        onChange={(e) => patchSlot(selectedSlot, { align: e.target.value })}
                        className="h-8 w-full rounded-md bg-black/30 border border-white/10 text-sm px-2"
                        data-testid="zayav-edit-align"
                      >
                        <option value="left">влево</option>
                        <option value="center">по центру</option>
                        <option value="right">вправо</option>
                      </select>
                    </div>
                    <label className="flex items-center gap-1 text-[12px] mt-4">
                      <input
                        type="checkbox"
                        checked={!!selCfg.bold}
                        onChange={(e) => patchSlot(selectedSlot, { bold: e.target.checked })}
                        data-testid="zayav-edit-bold"
                      />
                      жирный
                    </label>
                  </div>
                </div>
              ) : (
                <div className="text-[12px] text-muted-foreground">Поле не выбрано — кликните по полю в предпросмотре.</div>
              )}
              <div className="grid grid-cols-2 gap-2 pt-1">
                <Button onClick={doSaveLayout} disabled={savingLayout} className="bg-amber-500 hover:bg-amber-600 text-black" data-testid="zayav-save-layout">
                  <Save className="h-4 w-4 mr-1" /> {savingLayout ? "…" : "Сохранить раскладку"}
                </Button>
                <Button onClick={doResetLayout} disabled={savingLayout} variant="outline" data-testid="zayav-reset-layout">
                  Сбросить
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* ---- Preview ---- */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-muted-foreground">
              Предпросмотр — {page === 2 ? "страница 2 (оборот)" : "страница 1 (лицо)"}
            </div>
            <div className="flex items-center gap-2">
              <div className="flex rounded-md border border-white/10 overflow-hidden">
                <button
                  type="button"
                  onClick={() => setPage(1)}
                  className={`px-3 py-1.5 text-xs transition ${page === 1 ? "bg-[#E11D48] text-white font-semibold" : "text-muted-foreground hover:text-white"}`}
                  data-testid="zayav-page-1-btn"
                >
                  Стр. 1
                </button>
                <button
                  type="button"
                  onClick={() => setPage(2)}
                  className={`px-3 py-1.5 text-xs transition ${page === 2 ? "bg-[#E11D48] text-white font-semibold" : "text-muted-foreground hover:text-white"}`}
                  data-testid="zayav-page-2-btn"
                >
                  Стр. 2
                </button>
              </div>
              <Button
                size="sm"
                variant={editMode ? "default" : "ghost"}
                onClick={() => {
                  setEditMode((v) => !v);
                  setSelectedSlot(null);
                }}
                className={editMode ? "bg-amber-500 hover:bg-amber-600 text-black" : ""}
                data-testid="zayav-toggle-edit"
              >
                <SlidersHorizontal className="h-4 w-4 mr-1" /> {editMode ? "Готово" : "Настройка полей"}
              </Button>
            </div>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/5 p-3 shadow-2xl overflow-auto" style={{ maxHeight: "84vh" }}>
            <div className="mx-auto" style={{ maxWidth: 720 }}>
              <ZayavPreview
                page={page}
                backgroundUrl={zayavlenieBackgroundUrl(page)}
                slots={curSlots}
                values={values}
                editMode={editMode}
                selectedSlot={selectedSlot}
                onSelectSlot={setSelectedSlot}
                onChangeSlot={patchSlot}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
