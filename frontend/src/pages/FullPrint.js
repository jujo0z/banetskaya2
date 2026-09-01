import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useLocation } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Printer,
  Download,
  Shuffle,
  Eraser,
  FileText,
  Plus,
  Copy,
  Trash2,
  RefreshCw,
  ChevronDown,
} from "lucide-react";
import {
  getOverlayLayout,
  openOverlayPdf,
  downloadOverlayPdf,
  overlayPreviewPngUrl,
  getPrinters,
  printOverlaySilent,
  getRegProfile,
  listOverlayProfiles,
} from "@/lib/apiClient";
import { IS_DESKTOP } from "@/lib/env";
import { randomRecord, REQUIRED_KEYS } from "@/pages/BlankOverlay";

const recordLabel = (r, i) => (r && (r.fio || "").toString().trim()) || `Запись ${i + 1}`;

// Full print: complete СООБЩЕНИЕ forms laid out as a grid on real A4 pages.
export default function FullPrint() {
  const [layout, setLayout] = useState([]);
  const [baseLayout, setBaseLayout] = useState([]);
  const [profiles, setProfiles] = useState([]);
  const [activeProfileId, setActiveProfileId] = useState("");
  const [profileConstants, setProfileConstants] = useState({});
  const [records, setRecords] = useState([{}]);
  const [orientation, setOrientation] = useState("portrait"); // portrait=2/лист, landscape=4/лист
  const [perSheet, setPerSheet] = useState(2);
  const [activeIdx, setActiveIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewBusy, setPreviewBusy] = useState(false);
  // desktop silent printing
  const [printers, setPrinters] = useState([]);
  const [selectedPrinter, setSelectedPrinter] = useState("");
  const [printing, setPrinting] = useState(false);

  const location = useLocation();
  const profileRef = useRef({});
  const prevUrlRef = useRef(null);

  const maxPerSheet = orientation === "landscape" ? 4 : 2;

  // ---- prefill from reg-profile + contract(s) passed via history ----
  useEffect(() => {
    const prefill = location.state?.prefill || null;
    const prefillList = location.state?.prefillList || null;
    getRegProfile()
      .then((p) => {
        profileRef.current = p || {};
        applyPrefill(p || {}, prefill, prefillList);
      })
      .catch(() => applyPrefill({}, prefill, prefillList));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const applyPrefill = (profile, prefill, prefillList) => {
    const base = {};
    if (profile.reg_organ) base.reg_organ = profile.reg_organ;
    if (profile.chief) base.chief = profile.chief;
    let list = null;
    if (Array.isArray(prefillList) && prefillList.length) list = prefillList;
    else if (prefill) list = [prefill];
    if (list) {
      setRecords(list.map((r) => ({ ...base, ...r })));
      setActiveIdx(0);
      toast.success(`Подставлено записей: ${list.length}`);
    } else {
      setRecords([{ ...base }]);
    }
  };

  // ---- load layout + profiles ----
  useEffect(() => {
    (async () => {
      try {
        const data = await getOverlayLayout();
        const base = data.layout || [];
        setBaseLayout(base);
        setLayout(base);
      } catch (e) {
        toast.error("Не удалось загрузить раскладку");
      }
      try {
        const pd = await listOverlayProfiles();
        const list = pd.profiles || [];
        setProfiles(list);
        const act = list.find((p) => p.id === pd.active_id) || list[0] || null;
        if (act) {
          setActiveProfileId(act.id);
          const consts = {};
          Object.entries(act.constants || {}).forEach(([k, c]) => { consts[k] = (c && c.value) || ""; });
          setProfileConstants(consts);
          const custom = (act.layout || []).filter((f) => f.custom);
          setLayout((cur) => {
            const base = cur.length ? cur : [];
            return [...base.filter((f) => !f.custom), ...custom];
          });
          setRecords((rs) => rs.map((r) => ({ ...consts, ...r })));
        }
      } catch (e) {
        /* профили не критичны для полной печати */
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // ---- switch data profile: подставляет постоянные данные + добавленные поля ----
  const switchDataProfile = (id) => {
    const p = profiles.find((x) => x.id === id);
    if (!p) return;
    setActiveProfileId(id);
    const consts = {};
    Object.entries(p.constants || {}).forEach(([k, c]) => { consts[k] = (c && c.value) || ""; });
    setProfileConstants(consts);
    const custom = (p.layout || []).filter((f) => f.custom);
    setLayout([...baseLayout, ...custom]);
    setRecords((rs) => rs.map((r) => ({ ...r, ...consts })));
    toast.success(`Профиль «${p.name}» применён (постоянные данные подставлены)`);
  };

  // ---- load printers (desktop app only) ----
  useEffect(() => {
    if (!IS_DESKTOP) return;
    (async () => {
      try {
        const res = await getPrinters();
        if (res && res.supported && Array.isArray(res.printers)) {
          setPrinters(res.printers);
          const def = res.printers.find((p) => p.default) || res.printers[0];
          if (def) setSelectedPrinter(def.name);
        }
      } catch (e) {
        /* printing UI simply won't appear */
      }
    })();
  }, []);

  // keep perSheet within the allowed range when orientation changes
  useEffect(() => {
    setPerSheet((n) => Math.min(Math.max(1, n), maxPerSheet));
  }, [maxPerSheet]);

  const groups = useMemo(() => {
    const g = {};
    layout.forEach((f) => {
      const key = f.group || "Поля";
      (g[key] = g[key] || []).push(f);
    });
    return g;
  }, [layout]);

  const sheets = Math.max(1, Math.ceil(records.length / perSheet));

  const opts = useCallback(
    () => ({ layout, mode: "full", orientation, perSheet }),
    [layout, orientation, perSheet]
  );

  // ---- record helpers ----
  const setRecordVal = (idx, key, val) =>
    setRecords((rs) => rs.map((r, i) => (i === idx ? { ...r, [key]: val } : r)));

  const addRecord = () => {
    const base = { ...profileConstants };
    if (profileRef.current?.reg_organ && !base.reg_organ) base.reg_organ = profileRef.current.reg_organ;
    if (profileRef.current?.chief && !base.chief) base.chief = profileRef.current.chief;
    setRecords((rs) => {
      const next = [...rs, base];
      setActiveIdx(next.length - 1);
      return next;
    });
  };
  const duplicateRecord = (idx) =>
    setRecords((rs) => {
      const next = [...rs];
      next.splice(idx + 1, 0, { ...rs[idx] });
      setActiveIdx(idx + 1);
      return next;
    });
  const removeRecord = (idx) =>
    setRecords((rs) => {
      if (rs.length <= 1) return [{}];
      const next = rs.filter((_, i) => i !== idx);
      setActiveIdx((a) => Math.min(a, next.length - 1));
      return next;
    });
  const fillRandomAt = (idx) => {
    setRecords((rs) => rs.map((r, i) => (i === idx ? randomRecord() : r)));
    toast.success("Заполнено случайными данными");
  };
  const clearRecordAt = (idx) =>
    setRecords((rs) => rs.map((r, i) => (i === idx ? {} : r)));

  // ---- validation ----
  const validate = () => {
    for (let i = 0; i < records.length; i++) {
      const miss = REQUIRED_KEYS.filter((k) => !((records[i][k] || "").toString().trim()));
      if (miss.length) {
        setActiveIdx(i);
        toast.error(`Запись ${i + 1}: заполните обязательные поля (${miss.length})`);
        return false;
      }
    }
    return true;
  };

  // ---- live preview (debounced) ----
  const refreshPreview = useCallback(async () => {
    if (loading) return;
    setPreviewBusy(true);
    try {
      const url = await overlayPreviewPngUrl(records, opts());
      if (prevUrlRef.current) window.URL.revokeObjectURL(prevUrlRef.current);
      prevUrlRef.current = url;
      setPreviewUrl(url);
    } catch (e) {
      /* ignore preview errors */
    } finally {
      setPreviewBusy(false);
    }
  }, [records, opts, loading]);

  useEffect(() => {
    const t = setTimeout(refreshPreview, 500);
    return () => clearTimeout(t);
  }, [refreshPreview]);

  useEffect(() => () => {
    if (prevUrlRef.current) window.URL.revokeObjectURL(prevUrlRef.current);
  }, []);

  // ---- actions ----
  const doOpen = async () => {
    if (!validate()) return;
    try {
      await openOverlayPdf(records, opts());
      toast("PDF открыт — печатайте «Фактический размер» (100%)");
    } catch (e) {
      toast.error("Ошибка открытия PDF");
    }
  };
  const doDownload = async () => {
    try {
      await downloadOverlayPdf(records, opts());
    } catch (e) {
      toast.error("Ошибка скачивания");
    }
  };
  const doPrintSilent = async () => {
    if (!validate()) return;
    setPrinting(true);
    try {
      const res = await printOverlaySilent(records, { ...opts(), printerName: selectedPrinter });
      toast.success(`Отправлено на печать (${sheets} лист(ов)): ${res.printer}`);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Ошибка печати");
    } finally {
      setPrinting(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-muted-foreground">Загрузка…</div>;
  }

  return (
    <div className="p-6 lg:p-8 space-y-6" data-testid="fullprint-page">
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight flex items-center gap-3">
          <FileText className="h-8 w-8 text-[#EC4899]" /> Полная печать
        </h1>
        <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
          Печать целых бланков на обычной бумаге A4 — форма набирается заново + данные.
          Готовый бумажный бланк не нужен. Несколько сообщений размещаются на одном листе
          сеткой; выберите ориентацию и сколько бланков на лист.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[380px_minmax(0,1fr)] gap-6">
        {/* ---- Controls ---- */}
        <div className="space-y-4">
          {/* Data profile */}
          {profiles.length > 0 && (
            <div className="rounded-lg border border-[#EC4899]/30 bg-[#EC4899]/5 p-4 space-y-2" data-testid="fp-profile-box">
              <div className="text-sm font-semibold">Профиль данных</div>
              <select
                value={activeProfileId}
                onChange={(e) => switchDataProfile(e.target.value)}
                data-testid="fp-profile-select"
                className="w-full rounded-md bg-white border border-pink-200 px-3 py-2 text-sm outline-none focus:border-[#EC4899]"
              >
                {profiles.map((p) => (
                  <option key={p.id} value={p.id} className="bg-neutral-900">{p.name}</option>
                ))}
              </select>
              <p className="text-[11px] text-muted-foreground">
                Подставляет из профиля <b>постоянные данные</b> (орган, начальник и т.п.) и <b>добавленные поля</b>
                во все записи. Положение полей на A4 задаётся автоматически.
              </p>
            </div>
          )}

          {/* Layout settings */}
          <div className="rounded-lg border border-pink-100 bg-white/80 p-4 space-y-3">
            <div className="text-sm font-semibold flex items-center gap-2">
              <Printer className="h-4 w-4 text-[#EC4899]" /> Раскладка на листе
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setOrientation("portrait")}
                className={`rounded-md border px-3 py-2 text-sm text-left transition ${
                  orientation === "portrait" ? "border-[#EC4899] bg-[#EC4899]/10" : "border-pink-100 hover:border-pink-200"
                }`}
                data-testid="orient-portrait"
              >
                <div className="font-semibold">A4 книжная</div>
                <div className="text-[11px] text-muted-foreground">до 2 бланков</div>
              </button>
              <button
                type="button"
                onClick={() => setOrientation("landscape")}
                className={`rounded-md border px-3 py-2 text-sm text-left transition ${
                  orientation === "landscape" ? "border-[#EC4899] bg-[#EC4899]/10" : "border-pink-100 hover:border-pink-200"
                }`}
                data-testid="orient-landscape"
              >
                <div className="font-semibold">A4 альбомная</div>
                <div className="text-[11px] text-muted-foreground">до 4 бланков (2×2)</div>
              </button>
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Бланков на лист (макс. {maxPerSheet})</Label>
              <div className="flex gap-2 mt-1">
                {Array.from({ length: maxPerSheet }, (_, i) => i + 1).map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => setPerSheet(n)}
                    className={`flex-1 rounded-md border px-2 py-1.5 text-sm transition ${
                      perSheet === n ? "border-[#EC4899] bg-[#EC4899]/10 font-semibold" : "border-pink-100 hover:border-pink-200"
                    }`}
                    data-testid={`persheet-${n}`}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
            <div className="text-[12px] text-muted-foreground bg-white/80 rounded-md px-3 py-2">
              Записей: <b className="text-slate-800">{records.length}</b> · листов A4:{" "}
              <b className="text-slate-800">{sheets}</b>
            </div>
          </div>

          {/* Silent printing — desktop only */}
          {IS_DESKTOP && (
            <div className="rounded-lg border border-[#EC4899]/40 bg-[#EC4899]/5 p-3 space-y-2" data-testid="silent-print-box">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Printer className="h-4 w-4 text-[#EC4899]" /> Печать на принтер (без окон)
              </div>
              <select
                value={selectedPrinter}
                onChange={(e) => setSelectedPrinter(e.target.value)}
                data-testid="printer-select"
                className="w-full rounded-md bg-white border border-pink-200 px-3 py-2 text-sm outline-none focus:border-[#EC4899]"
              >
                {printers.length === 0 && <option value="">Принтеры не найдены</option>}
                {printers.map((p) => (
                  <option key={p.name} value={p.name} className="bg-neutral-900">
                    {p.name}{p.default ? " (по умолчанию)" : ""}
                  </option>
                ))}
              </select>
              <Button
                onClick={doPrintSilent}
                disabled={printing || printers.length === 0}
                className="w-full bg-[#EC4899] hover:bg-[#DB2777]"
                data-testid="btn-print-silent"
              >
                <Printer className="h-4 w-4 mr-2" />
                {printing ? "Печать…" : `Печать ${sheets} лист(ов) (тихо, 100%)`}
              </Button>
            </div>
          )}

          <div className="grid grid-cols-2 gap-2">
            <Button onClick={doOpen} className="bg-[#EC4899] hover:bg-[#DB2777]" data-testid="btn-open">
              <Printer className="h-4 w-4 mr-2" /> Открыть/Печать
            </Button>
            <Button onClick={doDownload} variant="outline" data-testid="btn-download">
              <Download className="h-4 w-4 mr-2" /> Скачать PDF
            </Button>
          </div>

          {/* Records manager */}
          <div className="rounded-lg border border-pink-100 bg-white/80 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold">Записи ({records.length})</div>
              <Button size="sm" variant="outline" onClick={addRecord} data-testid="btn-add-record">
                <Plus className="h-4 w-4 mr-1" /> Добавить
              </Button>
            </div>
            <div className="space-y-2 max-h-[520px] overflow-auto pr-1">
              {records.map((r, idx) => {
                const open = idx === activeIdx;
                return (
                  <div key={idx} className="rounded-md border border-pink-100 bg-white/60" data-testid={`record-${idx}`}>
                    <div className="flex items-center gap-1 px-2 py-1.5">
                      <button
                        type="button"
                        onClick={() => setActiveIdx(open ? -1 : idx)}
                        className="flex items-center gap-2 flex-1 min-w-0 text-left text-sm"
                        data-testid={`record-toggle-${idx}`}
                      >
                        <ChevronDown className={`h-4 w-4 shrink-0 transition-transform ${open ? "" : "-rotate-90"}`} />
                        <span className="truncate">{recordLabel(r, idx)}</span>
                      </button>
                      <button type="button" title="Случайные" onClick={() => fillRandomAt(idx)} className="p-1.5 text-muted-foreground hover:text-slate-900" data-testid={`record-random-${idx}`}>
                        <Shuffle className="h-3.5 w-3.5" />
                      </button>
                      <button type="button" title="Дублировать" onClick={() => duplicateRecord(idx)} className="p-1.5 text-muted-foreground hover:text-slate-900" data-testid={`record-dup-${idx}`}>
                        <Copy className="h-3.5 w-3.5" />
                      </button>
                      <button type="button" title="Очистить" onClick={() => clearRecordAt(idx)} className="p-1.5 text-muted-foreground hover:text-slate-900">
                        <Eraser className="h-3.5 w-3.5" />
                      </button>
                      <button type="button" title="Удалить" onClick={() => removeRecord(idx)} className="p-1.5 text-muted-foreground hover:text-[#EC4899]" data-testid={`record-del-${idx}`}>
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    {open && (
                      <div className="px-3 pb-3 pt-1 space-y-3 border-t border-pink-100">
                        {Object.entries(groups).map(([g, fs]) => (
                          <div key={g}>
                            <div className="text-[10px] uppercase tracking-wider text-[#EC4899] font-semibold mb-1.5">{g}</div>
                            <div className="space-y-1.5">
                              {fs.map((f) => (
                                <div key={f.key}>
                                  <Label className="text-[11px] text-muted-foreground">
                                    {f.label}
                                    {REQUIRED_KEYS.includes(f.key) && <span className="text-[#EC4899]"> *</span>}
                                  </Label>
                                  <Input
                                    value={r[f.key] || ""}
                                    onChange={(e) => setRecordVal(idx, f.key, e.target.value)}
                                    className="h-8 text-sm"
                                    data-testid={`input-${idx}-${f.key}`}
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
              Предпросмотр листа (так и напечатается)
            </div>
            <Button size="sm" variant="ghost" onClick={refreshPreview} disabled={previewBusy} data-testid="btn-refresh-preview">
              <RefreshCw className={`h-4 w-4 mr-1 ${previewBusy ? "animate-spin" : ""}`} /> Обновить
            </Button>
          </div>
          <div className="rounded-lg border border-pink-100 bg-white overflow-hidden shadow-2xl flex items-center justify-center" style={{ height: "78vh" }}>
            {previewUrl ? (
              <img src={previewUrl} alt="Предпросмотр листа" className="max-w-full max-h-full object-contain" data-testid="fullprint-preview" />
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
