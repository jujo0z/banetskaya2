import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import DuplexOffset from "@/components/DuplexOffset";
import { useLocation } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  ClipboardList,
  Printer,
  Download,
  Upload,
  Plus,
  Copy,
  Trash2,
  Eraser,
  RefreshCw,
  ChevronDown,
  Save,
  Wand2,
  PenSquare,
  Users,
} from "lucide-react";
import {
  forma19Fields,
  getForma19Defaults,
  saveForma19Defaults,
  forma19Prefill,
  forma19PreviewPngUrl,
  openForma19Pdf,
  downloadForma19Pdf,
  openPackagePdf,
  downloadPackagePdf,
  listContracts, getFormaTemplate, patchContractMaster,
} from "@/lib/apiClient";
import DocEditor from "@/components/DocEditor";
import ResidentPicker from "@/components/ResidentPicker";

const recordLabel = (r, i) => {
  const fio = [r.surname, r.first_name, r.patronymic].filter(Boolean).join(" ").trim();
  return fio || `Запись ${i + 1}`;
};

// Слот бланка Формы 19 -> какие поля БАЗЫ (master) его наполняют.
// Правка этих полей в списке сохраняется в единую базу и меняет данные везде.
const FORMA19_SLOT_MASTER = {
  surname: [["fio", "ФИО"]], first_name: [["fio", "ФИО"]], patronymic: [["fio", "ФИО"]],
  birth_day: [["birth_date", "Дата рождения"]], birth_month: [["birth_date", "Дата рождения"]], birth_year: [["birth_date", "Дата рождения"]],
  sex: [["sex", "Пол (1/2)"]], citizenship: [["citizenship", "Гражданство"]], id_number: [["id_number", "Идентификационный номер"]],
  bp_obl: [["bp_obl", "Место рожд.: обл."]], bp_raion: [["bp_raion", "Место рожд.: район"]], bp_city: [["bp_city", "Место рожд.: город"]], bp_village: [["bp_village", "Место рожд.: село"]],
  res_obl: [["res_obl", "Адрес: обл."]], res_raion: [["res_raion", "Адрес: район"]], res_city: [["res_city", "Адрес: город"]], res_village: [["res_village", "Адрес: село"]],
  res_street: [["res_street", "Улица"]], res_house: [["res_house", "Дом"]], res_korpus: [["res_korpus", "Корпус"]], res_apartment: [["res_apartment", "Комната/квартира"]],
  reg_authority: [["reg_organ", "Орган регистрации"]],
  from_obl: [["from_obl", "Откуда: обл."]], from_raion: [["from_raion", "Откуда: район"]], from_city: [["from_city", "Откуда: город"]], from_village: [["from_village", "Откуда: село"]],
  arrival_date: [["arrival_date", "Дата прибытия"]],
  purpose: [["purpose", "Цель приезда"]], purpose_term: [["purpose_term", "Срок пребывания"]],
  employment: [["prev_work", "Где и кем работал"]],
  passport_series: [["passport", "Паспорт (серия и номер)"]], passport_number: [["passport", "Паспорт (серия и номер)"]],
  passport_issued: [["passport_issued_by", "Паспорт: кем выдан"]], passport_issue_date: [["passport_issue_date", "Паспорт: дата выдачи"]],
};

// Форма 19 — «Адресный листок прибытия». Полная векторная печать на A4,
// сетка 2×2 = 2 человека на лист, по 2 копии; лицо + оборот для дуплекса.
export default function Forma19() {
  const [groups, setGroups] = useState([]);
  const [defaults, setDefaults] = useState({});
  const [records, setRecords] = useState([{}]);
  const [people, setPeople] = useState([]); // [{id, master}] — единая база; правки пишутся сюда
  const [templateFields, setTemplateFields] = useState([]); // слоты «Поле», реально стоящие в шаблоне
  const [activeIdx, setActiveIdx] = useState(0);
  const [duplexFlip, setDuplexFlip] = useState("long");
  const [loading, setLoading] = useState(true);
  const [showDefaults, setShowDefaults] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewBusy, setPreviewBusy] = useState(false);
  const [previewSide, setPreviewSide] = useState("front");
  const [editMode, setEditMode] = useState(false);
  const [uploading, setUploading] = useState(false); // eslint-disable-line no-unused-vars
  const [pickerOpen, setPickerOpen] = useState(false);
  const [savingDefaults, setSavingDefaults] = useState(false);
  const [masterRows, setMasterRows] = useState([]);
  const [packageBusy, setPackageBusy] = useState(false);

  const location = useLocation();
  const fileRef = useRef(null);
  const prevUrlRef = useRef(null);

  const allFields = useMemo(
    () => groups.flatMap((g) => g.fields),
    [groups]
  );

  const sheets = Math.max(1, Math.ceil(records.length / 2));

  // ---- initial load: fields + defaults (+ optional prefill from History) ----
  useEffect(() => {
    (async () => {
      try {
        const [f, d, tpl] = await Promise.all([forma19Fields(), getForma19Defaults(), getFormaTemplate(19)]);
        setGroups(f.groups || []);
        setDefaults(d || {});
        const tfields = [];
        (tpl && tpl.template || []).forEach((e) => { if (e && e.type === "field" && e.field) tfields.push(e.field); });
        setTemplateFields(tfields);
        const prefillList = location.state?.prefillList || null;
        if (Array.isArray(prefillList) && prefillList.length) {
          const recs = await forma19Prefill(prefillList);
          setRecords(recs.map((r) => ({ ...(d || {}), ...r })));
          setPeople(prefillList.map((c) => ({ id: c.id, master: { ...((c && c._master) || c || {}) } })));
          toast.success(`Подставлено записей: ${recs.length}`);
        } else {
          try {
            const all = await listContracts("", "");
            if (Array.isArray(all) && all.length) {
              const students = all.map((c) => ({ ...(c.fields || {}), _master: c.master || {} }));
              const recs = await forma19Prefill(students);
              setRecords((recs || []).map((r) => ({ ...(d || {}), ...r })));
              setMasterRows(all.map((c) => c.master || {}));
              setPeople(all.map((c) => ({ id: c.id, master: { ...(c.master || {}) } })));
              toast.success(`Загружена база: ${(recs || []).length}`);
            } else {
              setRecords([{ ...(d || {}) }]);
            }
          } catch (e2) {
            setRecords([{ ...(d || {}) }]);
          }
        }
      } catch (e) {
        toast.error("Не удалось загрузить поля Формы 19");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // ---- Подстановка из единой базы проживающих ----
  const onPickFromBase = async (picked) => {
    try {
      const students = picked.map((c) => ({ ...(c.fields || {}), _master: c.master || {} }));
      const recs = await forma19Prefill(students);
      setRecords((recs || []).map((r) => ({ ...defaults, ...r })));
      setMasterRows(picked.map((c) => c.master || {}));
      setPeople(picked.map((c) => ({ id: c.id, master: { ...(c.master || {}) } })));
      setActiveIdx(0);
      toast.success(`Подставлено из базы: ${recs.length}`);
    } catch (err) {
      toast.error("Не удалось подставить из базы проживающих");
    }
  };

  const onPackage = async (mode) => {
    if (!masterRows.length) {
      toast.error("Сначала загрузите Excel-шаблон «Данные»");
      return;
    }
    setPackageBusy(true);
    try {
      if (mode === "download") await downloadPackagePdf(masterRows, duplexFlip);
      else await openPackagePdf(masterRows, duplexFlip);
      toast.success("Полный пакет сформирован");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Ошибка формирования пакета");
    } finally {
      setPackageBusy(false);
    }
  };

  // ---- defaults (постоянные значения) ----
  const setDefaultVal = (key, val) => setDefaults((d) => ({ ...d, [key]: val }));
  const applyDefaultsToAll = () =>
    setRecords((rs) => rs.map((r) => ({ ...defaults, ...stripEmpty(r) })));
  const stripEmpty = (obj) => {
    const out = {};
    Object.entries(obj || {}).forEach(([k, v]) => {
      if (v !== undefined && v !== null && String(v).trim() !== "") out[k] = v;
    });
    return out;
  };
  const doSaveDefaults = async () => {
    setSavingDefaults(true);
    try {
      await saveForma19Defaults(stripEmpty(defaults));
      applyDefaultsToAll();
      toast.success("Постоянные значения сохранены и применены");
    } catch (e) {
      toast.error("Не удалось сохранить");
    } finally {
      setSavingDefaults(false);
    }
  };

  // ---- record helpers ----
  const setRecordVal = (idx, key, val) =>
    setRecords((rs) => rs.map((r, i) => (i === idx ? { ...r, [key]: val } : r)));

  // ---- Правка полей БАЗЫ прямо в списке (двусторонняя синхронизация) ----
  const rederiveTimers = useRef({});
  const persistTimers = useRef({});
  const rederiveOne = (idx, master, id) => {
    if (rederiveTimers.current[idx]) clearTimeout(rederiveTimers.current[idx]);
    rederiveTimers.current[idx] = setTimeout(async () => {
      try {
        const recs = await forma19Prefill([{ _master: master, id }]);
        if (recs && recs[0]) setRecords((rs) => rs.map((r, i) => (i === idx ? { ...defaults, ...recs[0] } : r)));
      } catch (e) { /* ignore */ }
    }, 350);
  };
  const persistMaster = (id, master) => {
    if (!id) return;
    if (persistTimers.current[id]) clearTimeout(persistTimers.current[id]);
    persistTimers.current[id] = setTimeout(() => { patchContractMaster(id, master).catch(() => {}); }, 800);
  };
  const setMasterVal = (idx, key, val) => {
    setPeople((ps) => {
      const np = ps.map((p, i) => (i === idx ? { ...p, master: { ...(p.master || {}), [key]: val } } : p));
      const p = np[idx];
      if (p) { rederiveOne(idx, p.master, p.id); persistMaster(p.id, p.master); }
      return np;
    });
  };
  // Поля БАЗЫ для правки = master-поля, стоящие за слотами шаблона (ячейки «Поле»).
  const editFields = useMemo(() => {
    const seen = new Set();
    const out = [];
    (templateFields || []).forEach((slot) => {
      let maps = FORMA19_SLOT_MASTER[slot];
      if (!maps && String(slot).indexOf("col:") === 0) maps = [[String(slot).slice(4), slot]];
      (maps || []).forEach(([mk, label]) => { if (!seen.has(mk)) { seen.add(mk); out.push({ key: mk, label }); } });
    });
    return out;
  }, [templateFields]);
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

  // ---- live preview (debounced) ----
  const refreshPreview = useCallback(async () => {
    if (loading) return;
    setPreviewBusy(true);
    try {
      const url = await forma19PreviewPngUrl(records, duplexFlip, previewSide);
      if (prevUrlRef.current) window.URL.revokeObjectURL(prevUrlRef.current);
      prevUrlRef.current = url;
      setPreviewUrl(url);
    } catch (e) {
      /* ignore */
    } finally {
      setPreviewBusy(false);
    }
  }, [records, duplexFlip, previewSide, loading]);

  useEffect(() => {
    const t = setTimeout(refreshPreview, 500);
    return () => clearTimeout(t);
  }, [refreshPreview]);
  useEffect(
    () => () => {
      if (prevUrlRef.current) window.URL.revokeObjectURL(prevUrlRef.current);
    },
    []
  );

  const doOpen = async () => {
    try {
      await openForma19Pdf(records, duplexFlip);
      toast("PDF открыт — печатайте «Фактический размер» (100%), двусторонняя печать");
    } catch (e) {
      toast.error("Ошибка открытия PDF");
    }
  };
  const doDownload = async () => {
    try {
      await downloadForma19Pdf(records, duplexFlip);
    } catch (e) {
      toast.error("Ошибка скачивания");
    }
  };

  if (loading) {
    return <div className="p-8 text-muted-foreground">Загрузка…</div>;
  }

  return (
    <div className="p-6 lg:p-8 space-y-6" data-testid="forma19-page">
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight flex items-center gap-3">
          <ClipboardList className="h-8 w-8 text-[#EC4899]" /> Адресный листок (Форма 19)
        </h1>
        <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
          Печать «Адресного листка прибытия» на чистой бумаге A4 — бланк рисуется заново + данные.
          На каждом листе <b>2 человека, по 2 копии</b> (сетка 2×2). Первый лист — лицевые
          стороны, второй — обороты, для двусторонней печати. Данные берутся из единой базы проживающих.
        </p>
      </div>


      <ResidentPicker
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        onPick={onPickFromBase}
        title="Выбрать проживающих для Формы 19"
      />

      <div className="grid grid-cols-1 lg:grid-cols-[400px_minmax(0,1fr)] gap-6">
        {/* ---- Controls ---- */}
        <div className="space-y-4">
          {/* Duplex flip */}
          <div className="rounded-lg border border-pink-100 bg-white/80 p-4 space-y-3">
            <div className="text-sm font-semibold flex items-center gap-2">
              <Printer className="h-4 w-4 text-[#EC4899]" /> Двусторонняя печать
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setDuplexFlip("long")}
                className={`rounded-md border px-3 py-2 text-sm text-left transition ${
                  duplexFlip === "long" ? "border-[#EC4899] bg-[#EC4899]/10" : "border-pink-100 hover:border-pink-200"
                }`}
                data-testid="f19-flip-long"
              >
                <div className="font-semibold">По длинному краю</div>
                <div className="text-[11px] text-muted-foreground">обычная (по умолчанию)</div>
              </button>
              <button
                type="button"
                onClick={() => setDuplexFlip("short")}
                className={`rounded-md border px-3 py-2 text-sm text-left transition ${
                  duplexFlip === "short" ? "border-[#EC4899] bg-[#EC4899]/10" : "border-pink-100 hover:border-pink-200"
                }`}
                data-testid="f19-flip-short"
              >
                <div className="font-semibold">По короткому краю</div>
                <div className="text-[11px] text-muted-foreground">если оборот не совпал</div>
              </button>
            </div>
            <div className="text-[12px] text-muted-foreground bg-white/80 rounded-md px-3 py-2">
              Людей: <b className="text-slate-800">{records.length}</b> · листов A4 (лицо+оборот):{" "}
              <b className="text-slate-800">{sheets}</b>
            </div>
          </div>

          <DuplexOffset testidPrefix="f19" />

          <div className="grid grid-cols-2 gap-2">
            <Button onClick={doOpen} className="bg-[#EC4899] hover:bg-[#DB2777]" data-testid="f19-open">
              <Printer className="h-4 w-4 mr-2" /> Открыть/Печать
            </Button>
            <Button onClick={doDownload} variant="outline" data-testid="f19-download">
              <Download className="h-4 w-4 mr-2" /> Скачать PDF
            </Button>
          </div>

          {/* Список проживающих (единая база) */}
          <div className="rounded-lg border border-pink-100 bg-white/80 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold">Проживающие ({records.length})</div>
            </div>
            <p className="text-[11px] text-muted-foreground">Раскройте человека, чтобы вручную поправить данные — правки сразу сохраняются в единую базу проживающих. Набор полей зависит от того, какие поля стоят в шаблоне.</p>
            <div className="space-y-2 max-h-[560px] overflow-auto pr-1">
              {records.map((r, idx) => {
                const open = idx === activeIdx;
                const m = (people[idx] && people[idx].master) || {};
                const room = m.room_number ? `комн. ${m.room_number}` : "";
                return (
                  <div key={idx} className="rounded-md border border-pink-100 bg-white/60" data-testid={`f19-record-${idx}`}>
                    <div className="flex items-center gap-1 px-2 py-1.5">
                      <button
                        type="button"
                        onClick={() => setActiveIdx(open ? -1 : idx)}
                        className="flex items-center gap-2 flex-1 min-w-0 text-left text-sm"
                        data-testid={`f19-record-toggle-${idx}`}
                      >
                        <ChevronDown className={`h-4 w-4 shrink-0 transition-transform ${open ? "" : "-rotate-90"}`} />
                        <span className="truncate">{recordLabel(r, idx)}</span>
                        {room && <span className="ml-auto shrink-0 text-[11px] text-muted-foreground">{room}</span>}
                      </button>
                    </div>
                    {open && (
                      <div className="px-3 pb-3 pt-1 space-y-1.5 border-t border-pink-100">
                        {editFields.length === 0 ? (
                          <p className="text-[11px] text-muted-foreground pt-2">
                            В шаблоне нет полей данных. Включите «Редактор шаблона» и добавьте поля кнопкой «Поле» — здесь появятся соответствующие данные из базы для ручной правки.
                          </p>
                        ) : (
                          editFields.map((f) => (
                            <div key={f.key}>
                              <Label className="text-[11px] text-muted-foreground">{f.label}</Label>
                              <Input
                                value={m[f.key] || ""}
                                onChange={(e) => setMasterVal(idx, f.key, e.target.value)}
                                className="h-8 text-sm"
                                data-testid={`f19-input-${idx}-${f.key}`}
                              />
                            </div>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* ---- Preview ---- */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-muted-foreground">
              {editMode ? "Редактор шаблона Формы 19" : `Предпросмотр листа (${previewSide === "back" ? "оборотная сторона" : "лицевая сторона"})`}
            </div>
            <div className="flex items-center gap-2">
              {!editMode && (
                <div className="flex rounded-md border border-pink-100 overflow-hidden">
                  <button
                    type="button"
                    onClick={() => setPreviewSide("front")}
                    className={`px-3 py-1.5 text-xs transition ${previewSide === "front" ? "bg-[#EC4899] text-white font-semibold" : "text-muted-foreground hover:text-slate-900"}`}
                    data-testid="f19-side-front"
                  >
                    Лицевая
                  </button>
                  <button
                    type="button"
                    onClick={() => setPreviewSide("back")}
                    className={`px-3 py-1.5 text-xs transition ${previewSide === "back" ? "bg-[#EC4899] text-white font-semibold" : "text-muted-foreground hover:text-slate-900"}`}
                    data-testid="f19-side-back"
                  >
                    Оборотная
                  </button>
                </div>
              )}
              {!editMode && (
                <Button size="sm" variant="ghost" onClick={refreshPreview} disabled={previewBusy} data-testid="f19-refresh-preview">
                  <RefreshCw className={`h-4 w-4 mr-1 ${previewBusy ? "animate-spin" : ""}`} /> Обновить
                </Button>
              )}
              <Button
                size="sm"
                variant={editMode ? "default" : "outline"}
                onClick={() => setEditMode((v) => !v)}
                className={editMode ? "bg-amber-500 hover:bg-amber-600 text-black" : ""}
                data-testid="f19-toggle-edit"
              >
                <PenSquare className="h-4 w-4 mr-1" /> {editMode ? "Готово" : "Редактор шаблона"}
              </Button>
            </div>
          </div>
          {editMode ? (
            <DocEditor
              which={19}
              values={records[activeIdx >= 0 ? activeIdx : 0] || {}}
              side={previewSide}
              setSide={setPreviewSide}
            />
          ) : (
            <div className="rounded-lg border border-pink-100 bg-white overflow-hidden shadow-2xl flex items-center justify-center" style={{ height: "80vh" }}>
              {previewUrl ? (
                <img src={previewUrl} alt="Предпросмотр Формы 19" className="max-w-full max-h-full object-contain" data-testid="forma19-preview" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                  Формирование предпросмотра…
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
