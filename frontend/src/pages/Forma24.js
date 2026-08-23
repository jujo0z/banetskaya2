import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
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
} from "lucide-react";
import {
  forma24Fields,
  getForma24Defaults,
  saveForma24Defaults,
  forma24Prefill,
  forma24PreviewPngUrl,
  openForma24Pdf,
  downloadForma24Pdf,
  masterUpload,
  downloadMasterTemplate,
  openPackagePdf,
  downloadPackagePdf,
} from "@/lib/apiClient";

const recordLabel = (r, i) => {
  const fio = [r.surname, r.first_name, r.patronymic].filter(Boolean).join(" ").trim();
  return fio || `Запись ${i + 1}`;
};

// Форма 19 — «Адресный листок прибытия». Полная векторная печать на A4,
// сетка 2×2 = 2 человека на лист, по 2 копии; лицо + оборот для дуплекса.
export default function Forma24() {
  const [groups, setGroups] = useState([]);
  const [defaults, setDefaults] = useState({});
  const [records, setRecords] = useState([{}]);
  const [activeIdx, setActiveIdx] = useState(0);
  const [duplexFlip, setDuplexFlip] = useState("long");
  const [loading, setLoading] = useState(true);
  const [showDefaults, setShowDefaults] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewBusy, setPreviewBusy] = useState(false);
  const [previewSide, setPreviewSide] = useState("front");
  const [uploading, setUploading] = useState(false);
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
        const [f, d] = await Promise.all([forma24Fields(), getForma24Defaults()]);
        setGroups(f.groups || []);
        setDefaults(d || {});
        const prefillList = location.state?.prefillList || null;
        if (Array.isArray(prefillList) && prefillList.length) {
          const recs = await forma24Prefill(prefillList);
          setRecords(recs.map((r) => ({ ...(d || {}), ...r })));
          toast.success(`Подставлено записей: ${recs.length}`);
        } else {
          setRecords([{ ...(d || {}) }]);
        }
      } catch (e) {
        toast.error("Не удалось загрузить поля Формы 24");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // ---- Excel upload -> autofill (единый шаблон «Данные») ----
  const onUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const data = await masterUpload(file);
      const recs = data.forma24 || [];
      if (!recs.length) {
        toast.error("В файле не найдено данных");
      } else {
        setRecords(recs.map((r) => ({ ...defaults, ...r })));
        setMasterRows(data.master || []);
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
      await saveForma24Defaults(stripEmpty(defaults));
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
      const url = await forma24PreviewPngUrl(records, duplexFlip, previewSide);
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
      await openForma24Pdf(records, duplexFlip);
      toast("PDF открыт — печатайте «Фактический размер» (100%), двусторонняя печать");
    } catch (e) {
      toast.error("Ошибка открытия PDF");
    }
  };
  const doDownload = async () => {
    try {
      await downloadForma24Pdf(records, duplexFlip);
    } catch (e) {
      toast.error("Ошибка скачивания");
    }
  };

  if (loading) {
    return <div className="p-8 text-muted-foreground">Загрузка…</div>;
  }

  return (
    <div className="p-6 lg:p-8 space-y-6" data-testid="forma24-page">
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight flex items-center gap-3">
          <ClipboardList className="h-8 w-8 text-[#E11D48]" /> Талон учёта (Форма 24)
        </h1>
        <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
          Печать «Талона миграционного учёта к адресному листку прибытия» (Форма 24) на чистой бумаге A4 — бланк рисуется заново + данные.
          На каждом листе <b>2 человека, по 2 копии</b> (сетка 2×2). Первый лист — лицевые
          стороны, второй — обороты, для двусторонней печати. Автозаполнение из Excel со студентами.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[400px_minmax(0,1fr)] gap-6">
        {/* ---- Controls ---- */}
        <div className="space-y-4">
          {/* Excel upload */}
          <div className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-2">
            <div className="text-sm font-semibold flex items-center gap-2">
              <Upload className="h-4 w-4 text-[#E11D48]" /> Загрузка студентов из Excel
            </div>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.xlsm"
              onChange={onUpload}
              className="hidden"
              data-testid="f24-file-input"
            />
            <Button
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              variant="outline"
              className="w-full"
              data-testid="f24-upload-btn"
            >
              <Upload className="h-4 w-4 mr-2" />
              {uploading ? "Загрузка…" : "Выбрать .xlsx файл"}
            </Button>
            <Button
              onClick={onDownloadTemplate}
              variant="ghost"
              className="w-full text-[#E11D48] hover:text-[#E11D48]"
              data-testid="f24-download-template-btn"
            >
              <Download className="h-4 w-4 mr-2" />
              Скачать шаблон Excel
            </Button>
            <p className="text-[11px] text-muted-foreground">
              Единый шаблон «Данные»: одна строка = один человек = все документы (договор,
              сообщение, Форма 19 и 24). Первая строка уже заполнена примером.
            </p>
          </div>

          {/* Полный пакет документов */}
          <div className="rounded-lg border border-[#E11D48]/30 bg-gradient-to-br from-[#E11D48]/10 to-transparent p-4 space-y-2" data-testid="f24-package-box">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <ClipboardList className="h-4 w-4 text-[#E11D48]" /> Полный пакет документов
            </div>
            <p className="text-[11px] text-muted-foreground">
              Один PDF по каждому человеку: договор, лист «Форма 19 + Форма 24» (по 2 копии,
              обе формы на одном листе) и лист «Сообщение».
              {masterRows.length > 0 ? ` Загружено человек: ${masterRows.length}.` : " Сначала загрузите Excel-шаблон."}
            </p>
            <div className="flex gap-2">
              <Button
                onClick={() => onPackage("open")}
                disabled={packageBusy || !masterRows.length}
                className="flex-1 bg-[#E11D48] hover:bg-[#be123c] text-white"
                data-testid="f24-package-open-btn"
              >
                <Printer className="h-4 w-4 mr-2" />
                {packageBusy ? "Формирование…" : "Открыть пакет"}
              </Button>
              <Button
                onClick={() => onPackage("download")}
                disabled={packageBusy || !masterRows.length}
                variant="outline"
                data-testid="f24-package-download-btn"
              >
                <Download className="h-4 w-4" />
              </Button>
            </div>
          </div>


          {/* Постоянные значения (constants) */}
          <div className="rounded-lg border border-[#E11D48]/30 bg-[#E11D48]/5 p-4 space-y-2" data-testid="f24-defaults-box">
            <button
              type="button"
              onClick={() => setShowDefaults((s) => !s)}
              className="flex w-full items-center justify-between text-sm font-semibold"
              data-testid="f24-defaults-toggle"
            >
              <span className="flex items-center gap-2">
                <Wand2 className="h-4 w-4 text-[#E11D48]" /> Постоянные значения
              </span>
              <ChevronDown className={`h-4 w-4 transition-transform ${showDefaults ? "" : "-rotate-90"}`} />
            </button>
            <p className="text-[11px] text-muted-foreground">
              Задайте один раз (адрес общежития, орган регистрации, цель приезда и т.п.) — они
              подставятся во все листки. Данные студента из Excel имеют приоритет.
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
                            data-testid={`f24-default-${f.key}`}
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
              data-testid="f24-save-defaults"
            >
              <Save className="h-4 w-4 mr-2" />
              {savingDefaults ? "Сохранение…" : "Сохранить и применить ко всем"}
            </Button>
          </div>

          {/* Duplex flip */}
          <div className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
            <div className="text-sm font-semibold flex items-center gap-2">
              <Printer className="h-4 w-4 text-[#E11D48]" /> Двусторонняя печать
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setDuplexFlip("long")}
                className={`rounded-md border px-3 py-2 text-sm text-left transition ${
                  duplexFlip === "long" ? "border-[#E11D48] bg-[#E11D48]/10" : "border-white/10 hover:border-white/30"
                }`}
                data-testid="f24-flip-long"
              >
                <div className="font-semibold">По длинному краю</div>
                <div className="text-[11px] text-muted-foreground">обычная (по умолчанию)</div>
              </button>
              <button
                type="button"
                onClick={() => setDuplexFlip("short")}
                className={`rounded-md border px-3 py-2 text-sm text-left transition ${
                  duplexFlip === "short" ? "border-[#E11D48] bg-[#E11D48]/10" : "border-white/10 hover:border-white/30"
                }`}
                data-testid="f24-flip-short"
              >
                <div className="font-semibold">По короткому краю</div>
                <div className="text-[11px] text-muted-foreground">если оборот не совпал</div>
              </button>
            </div>
            <div className="text-[12px] text-muted-foreground bg-white/5 rounded-md px-3 py-2">
              Людей: <b className="text-white">{records.length}</b> · листов A4 (лицо+оборот):{" "}
              <b className="text-white">{sheets}</b>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <Button onClick={doOpen} className="bg-[#E11D48] hover:bg-[#BE123C]" data-testid="f24-open">
              <Printer className="h-4 w-4 mr-2" /> Открыть/Печать
            </Button>
            <Button onClick={doDownload} variant="outline" data-testid="f24-download">
              <Download className="h-4 w-4 mr-2" /> Скачать PDF
            </Button>
          </div>

          {/* Records manager */}
          <div className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold">Люди ({records.length})</div>
              <Button size="sm" variant="outline" onClick={addRecord} data-testid="f24-add-record">
                <Plus className="h-4 w-4 mr-1" /> Добавить
              </Button>
            </div>
            <div className="space-y-2 max-h-[520px] overflow-auto pr-1">
              {records.map((r, idx) => {
                const open = idx === activeIdx;
                return (
                  <div key={idx} className="rounded-md border border-white/10 bg-black/20" data-testid={`f24-record-${idx}`}>
                    <div className="flex items-center gap-1 px-2 py-1.5">
                      <button
                        type="button"
                        onClick={() => setActiveIdx(open ? -1 : idx)}
                        className="flex items-center gap-2 flex-1 min-w-0 text-left text-sm"
                        data-testid={`f24-record-toggle-${idx}`}
                      >
                        <ChevronDown className={`h-4 w-4 shrink-0 transition-transform ${open ? "" : "-rotate-90"}`} />
                        <span className="truncate">{recordLabel(r, idx)}</span>
                      </button>
                      <button type="button" title="Дублировать" onClick={() => duplicateRecord(idx)} className="p-1.5 text-muted-foreground hover:text-white" data-testid={`f24-record-dup-${idx}`}>
                        <Copy className="h-3.5 w-3.5" />
                      </button>
                      <button type="button" title="Очистить" onClick={() => clearRecordAt(idx)} className="p-1.5 text-muted-foreground hover:text-white">
                        <Eraser className="h-3.5 w-3.5" />
                      </button>
                      <button type="button" title="Удалить" onClick={() => removeRecord(idx)} className="p-1.5 text-muted-foreground hover:text-[#E11D48]" data-testid={`f24-record-del-${idx}`}>
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
                                    data-testid={`f24-input-${idx}-${f.key}`}
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
        </div>

        {/* ---- Preview ---- */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-muted-foreground">
              Предпросмотр листа ({previewSide === "back" ? "оборотная сторона" : "лицевая сторона"})
            </div>
            <div className="flex items-center gap-2">
              <div className="flex rounded-md border border-white/10 overflow-hidden">
                <button
                  type="button"
                  onClick={() => setPreviewSide("front")}
                  className={`px-3 py-1.5 text-xs transition ${previewSide === "front" ? "bg-[#E11D48] text-white font-semibold" : "text-muted-foreground hover:text-white"}`}
                  data-testid="f24-side-front"
                >
                  Лицевая
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewSide("back")}
                  className={`px-3 py-1.5 text-xs transition ${previewSide === "back" ? "bg-[#E11D48] text-white font-semibold" : "text-muted-foreground hover:text-white"}`}
                  data-testid="f24-side-back"
                >
                  Оборотная
                </button>
              </div>
              <Button size="sm" variant="ghost" onClick={refreshPreview} disabled={previewBusy} data-testid="f24-refresh-preview">
                <RefreshCw className={`h-4 w-4 mr-1 ${previewBusy ? "animate-spin" : ""}`} /> Обновить
              </Button>
            </div>
          </div>
          <div className="rounded-lg border border-white/10 bg-white overflow-hidden shadow-2xl flex items-center justify-center" style={{ height: "80vh" }}>
            {previewUrl ? (
              <img src={previewUrl} alt="Предпросмотр Формы 24" className="max-w-full max-h-full object-contain" data-testid="forma24-preview" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                Формирование предпросмотра…
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
