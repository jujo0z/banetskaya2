import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Stamp,
  Shuffle,
  Eye,
  Printer,
  Save,
  Crosshair,
  Plus,
  Minus,
  RotateCcw,
  Download,
  Info,
} from "lucide-react";
import {
  getOverlayLayout,
  saveOverlayLayout,
  overlayPdfUrl,
  openOverlayPdf,
  downloadOverlayPdf,
  openOverlayTestSheet,
  getPrinters,
  printOverlaySilent,
} from "@/lib/apiClient";
import { IS_DESKTOP } from "@/lib/env";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const BG_URL = `${BACKEND_URL}/api/overlay/background`;
// Physical page: 147 x 103 mm (landscape). Points = mm / 25.4 * 72.
const PAGE_W_PT = (147 / 25.4) * 72; // ~416.69

// Random demo data (Belarusian-style) — everything EXCEPT the signature.
const RAND = {
  fio: [
    "Иванов Иван Иванович,",
    "Петрова Мария Сергеевна,",
    "Сидоров Алексей Николаевич,",
    "Кузнецова Ольга Дмитриевна,",
  ],
  birth: ["1998 г.р., г. Минск", "2001 г.р., г. Гомель", "1995 г.р., г. Мозырь", "2000 г.р., г. Брест"],
  address: [
    "г. Мозырь, ул. Ленинская, д. 12, кв. 45",
    "г. Мозырь, б-р Юности, д. 30, комн. 210",
    "г. Мозырь, ул. Советская, д. 7, кв. 3",
  ],
  months: ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"],
  organ: ["Отдел по гражданству и миграции", "ОГиМ Мозырского РОВД"],
  issuedBy: ["Мозырским РОВД", "Гомельским ГОВД", "Минским РУВД"],
  chief: ["Ковалёв А.А.", "Соколова Н.В.", "Дубина И.П."],
  series: ["MP", "MC", "KH", "PP"],
};
const pick = (a) => a[Math.floor(Math.random() * a.length)];
const pad2 = (n) => String(n).padStart(2, "0");

export function randomRecord() {
  const d = 1 + Math.floor(Math.random() * 28);
  const m = pick(RAND.months);
  const y = 24 + Math.floor(Math.random() * 3);
  return {
    reg_organ: pick(RAND.organ),
    date_day: pad2(d),
    date_month: m,
    date_year: pad2(y),
    number: String(1000 + Math.floor(Math.random() * 8999)),
    fio: pick(RAND.fio),
    fio2: "",
    birth: pick(RAND.birth),
    address: pick(RAND.address),
    address2: "",
    passport_series: pick(RAND.series),
    passport_number: String(1000000 + Math.floor(Math.random() * 8999999)),
    issue_day: pad2(1 + Math.floor(Math.random() * 28)),
    issue_month: pick(RAND.months),
    issue_year: pad2(18 + Math.floor(Math.random() * 6)),
    issued_by: pick(RAND.issuedBy),
    from_day: pad2(d),
    from_month: m,
    from_year: pad2(y),
    to_day: pad2(d),
    to_month: m,
    to_year: pad2(y + 1),
    chief: pick(RAND.chief),
  };
}

export default function BlankOverlay() {
  const [layout, setLayout] = useState([]);
  const [values, setValues] = useState({});
  const [dx, setDx] = useState(0);
  const [dy, setDy] = useState(0);
  const [pageSize, setPageSize] = useState("a4");
  const [selected, setSelected] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [cw, setCw] = useState(700);
  // Silent printing (desktop app only)
  const [printers, setPrinters] = useState([]);
  const [selectedPrinter, setSelectedPrinter] = useState("");
  const [printing, setPrinting] = useState(false);

  const canvasRef = useRef(null);
  const dragRef = useRef(null);

  // ---- load layout ----
  useEffect(() => {
    (async () => {
      try {
        const data = await getOverlayLayout();
        setLayout(data.layout || []);
        setDx(data.dx_mm || 0);
        setDy(data.dy_mm || 0);
      } catch (e) {
        toast.error("Не удалось загрузить раскладку");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

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
        // printing UI simply won't appear if this fails
      }
    })();
  }, []);

  // ---- measure canvas width for font scaling ----
  useEffect(() => {
    const measure = () => {
      if (canvasRef.current) setCw(canvasRef.current.clientWidth);
    };
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [loading]);

  const groups = useMemo(() => {
    const g = {};
    layout.forEach((f) => {
      const key = f.group || "Поля";
      (g[key] = g[key] || []).push(f);
    });
    return g;
  }, [layout]);

  const scale = cw / PAGE_W_PT; // px per pt on screen

  const setVal = (k, v) => setValues((s) => ({ ...s, [k]: v }));

  const fillRandom = () => {
    setValues(randomRecord());
    toast.success("Заполнено случайными данными");
  };
  const clearAll = () => {
    setValues({});
    toast("Поля очищены");
  };

  // ---- dragging ----
  const onPointerDown = (e, key) => {
    e.preventDefault();
    e.stopPropagation();
    setSelected(key);
    dragRef.current = { key };
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
  };
  const onPointerMove = useCallback((e) => {
    if (!dragRef.current || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    let xp = ((e.clientX - rect.left) / rect.width) * 100;
    let yp = ((e.clientY - rect.top) / rect.height) * 100;
    xp = Math.max(0, Math.min(100, xp));
    yp = Math.max(0, Math.min(100, yp));
    const key = dragRef.current.key;
    setLayout((prev) => prev.map((f) => (f.key === key ? { ...f, x_pct: +xp.toFixed(2), y_pct: +yp.toFixed(2) } : f)));
  }, []);
  const onPointerUp = useCallback(() => {
    dragRef.current = null;
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", onPointerUp);
  }, [onPointerMove]);

  const changeFont = (key, delta) =>
    setLayout((prev) => prev.map((f) => (f.key === key ? { ...f, font_pt: Math.max(5, Math.min(20, (f.font_pt || 9) + delta)) } : f)));

  // ---- actions ----
  const doPreview = async () => {
    try {
      const url = await overlayPdfUrl([values], { layout, dx_mm: dx, dy_mm: dy, withBackground: true });
      setPreviewUrl(url);
      setPreviewOpen(true);
    } catch (e) {
      toast.error("Ошибка предпросмотра");
    }
  };
  const doPrint = async () => {
    try {
      await openOverlayPdf([values], { layout, dx_mm: dx, dy_mm: dy, pageSize });
      toast("PDF открыт в новой вкладке — печатайте с масштабом «Фактический размер» (100%)");
    } catch (e) {
      toast.error("Ошибка печати");
    }
  };
  const doPrintSilent = async () => {
    setPrinting(true);
    try {
      // Silent printing goes straight to the printer with the physical 147×103 blank
      // pre-inserted — always print at the real card size so the data lands exactly.
      const res = await printOverlaySilent([values], {
        layout, dx_mm: dx, dy_mm: dy, pageSize: "card", printerName: selectedPrinter,
      });
      toast.success(`Отправлено на печать (147×103 мм): ${res.printer}`);
    } catch (e) {
      const msg = e?.response?.data?.detail || "Ошибка печати";
      toast.error(msg);
    } finally {
      setPrinting(false);
    }
  };
  const doDownload = async () => {
    try {
      await downloadOverlayPdf([values], { layout, dx_mm: dx, dy_mm: dy, pageSize });
    } catch (e) {
      toast.error("Ошибка скачивания");
    }
  };
  const doSave = async () => {
    try {
      await saveOverlayLayout(layout, dx, dy);
      toast.success("Раскладка и калибровка сохранены");
    } catch (e) {
      toast.error("Не удалось сохранить");
    }
  };
  const doTestSheet = async () => {
    try {
      await openOverlayTestSheet(dx, dy, pageSize);
      toast("Пробный лист открыт — печатайте с масштабом 100%");
    } catch (e) {
      toast.error("Ошибка пробного листа");
    }
  };
  const resetLayout = async () => {
    try {
      // reload default by clearing saved value is not exposed; just refetch (server default if none saved)
      const data = await getOverlayLayout();
      setLayout(data.layout || []);
      toast("Раскладка перезагружена");
    } catch (e) {
      toast.error("Ошибка");
    }
  };

  if (loading) {
    return <div className="text-muted-foreground">Загрузка редактора…</div>;
  }

  const selField = layout.find((f) => f.key === selected);

  return (
    <div data-testid="blank-overlay-page">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-8">
        <div>
          <h1 className="font-heading text-4xl font-bold flex items-center gap-3">
            <Stamp className="h-8 w-8 text-[#E11D48]" /> Печать на бланке
          </h1>
          <p className="text-muted-foreground mt-2 max-w-2xl">
            Бланк «СООБЩЕНИЕ» (147×103&nbsp;мм). Данные печатаются поверх уже
            распечатанного бланка. Перетащите поля мышкой, чтобы попасть в строки,
            затем откалибруйте под ваш принтер.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 justify-end">
          <Button variant="outline" onClick={fillRandom} data-testid="btn-random">
            <Shuffle className="h-4 w-4 mr-2" /> Случайные данные
          </Button>
          <Button variant="outline" onClick={clearAll}>Очистить</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_360px] gap-6">
        {/* ---- Canvas ---- */}
        <div>
          <div
            ref={canvasRef}
            className="relative w-full rounded-lg overflow-hidden border border-white/10 shadow-2xl select-none bg-white"
            style={{ aspectRatio: "147 / 103" }}
            onPointerDown={() => setSelected(null)}
            data-testid="overlay-canvas"
          >
            <img
              src={BG_URL}
              alt="Бланк"
              className="absolute inset-0 w-full h-full object-fill pointer-events-none"
              draggable={false}
            />
            {layout.map((f) => {
              const v = values[f.key];
              const isSel = f.key === selected;
              const fontPx = Math.max(7, (f.font_pt || 9) * scale);
              return (
                <div
                  key={f.key}
                  onPointerDown={(e) => onPointerDown(e, f.key)}
                  className={`absolute cursor-move whitespace-nowrap leading-none px-0.5 rounded-sm transition-shadow ${
                    isSel ? "ring-2 ring-[#E11D48] bg-[#E11D48]/10" : "hover:ring-1 hover:ring-[#E11D48]/50"
                  }`}
                  style={{
                    left: `${f.x_pct}%`,
                    top: `${f.y_pct}%`,
                    fontSize: `${fontPx}px`,
                    color: v ? "#0a0a1f" : "#c026a1",
                    transform: "translate(0, -0.9em)",
                    fontFamily: "Arial, sans-serif",
                  }}
                  title={f.label}
                  data-testid={`field-box-${f.key}`}
                >
                  {v || f.label}
                </div>
              );
            })}
          </div>
          <p className="text-xs text-muted-foreground mt-2">
            Розовым показаны пустые поля (их подписи) — при печати они не выводятся.
            Тяните любое поле, чтобы поставить его точно на нужную строку.
          </p>
        </div>

        {/* ---- Side panel ---- */}
        <div className="space-y-5">
          {/* Selected field tools */}
          {selField && (
            <div className="rounded-lg border border-[#E11D48]/40 bg-[#E11D48]/5 p-4">
              <div className="text-sm font-semibold mb-2">Поле: {selField.label}</div>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted-foreground">Размер шрифта</span>
                <Button size="icon" variant="outline" className="h-7 w-7" onClick={() => changeFont(selField.key, -1)}>
                  <Minus className="h-3 w-3" />
                </Button>
                <span className="w-8 text-center font-mono">{selField.font_pt || 9}</span>
                <Button size="icon" variant="outline" className="h-7 w-7" onClick={() => changeFont(selField.key, 1)}>
                  <Plus className="h-3 w-3" />
                </Button>
              </div>
              <div className="text-[11px] text-muted-foreground mt-2 font-mono">
                X {selField.x_pct}% · Y {selField.y_pct}%
              </div>
            </div>
          )}

          {/* Paper size */}
          <div className="rounded-lg border border-white/10 bg-white/5 p-4">
            <div className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Printer className="h-4 w-4 text-[#E11D48]" /> Размер листа для печати
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setPageSize("a4")}
                className={`rounded-md border px-3 py-2 text-sm text-left transition ${
                  pageSize === "a4" ? "border-[#E11D48] bg-[#E11D48]/10" : "border-white/10 hover:border-white/30"
                }`}
                data-testid="paper-a4"
              >
                <div className="font-semibold">Лист A4</div>
                <div className="text-[11px] text-muted-foreground">рекомендуется · бланк в углу</div>
              </button>
              <button
                type="button"
                onClick={() => setPageSize("card")}
                className={`rounded-md border px-3 py-2 text-sm text-left transition ${
                  pageSize === "card" ? "border-[#E11D48] bg-[#E11D48]/10" : "border-white/10 hover:border-white/30"
                }`}
                data-testid="paper-card"
              >
                <div className="font-semibold">147×103 мм</div>
                <div className="text-[11px] text-muted-foreground">точно по размеру бланка</div>
              </button>
            </div>
            <div className="mt-3 flex gap-2 text-[11px] text-muted-foreground bg-amber-500/10 border border-amber-500/20 rounded-md p-2">
              <Info className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
              <span>
                Если принтер «выплёвывает» пустой лист — выберите <b>A4</b> и в окне печати
                поставьте масштаб <b>«Фактический размер» (100%)</b>, а не «По размеру страницы».
                Для A4: положите бланк в <b>левый верхний угол</b> листа (по рамке-подсказке).
              </span>
            </div>
          </div>

          {/* Calibration */}
          <div className="rounded-lg border border-white/10 bg-white/5 p-4">
            <div className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Crosshair className="h-4 w-4 text-[#E11D48]" /> Калибровка принтера
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs">Сдвиг X, мм</Label>
                <Input
                  type="number"
                  step="0.5"
                  value={dx}
                  onChange={(e) => setDx(parseFloat(e.target.value) || 0)}
                  data-testid="cal-dx"
                />
              </div>
              <div>
                <Label className="text-xs">Сдвиг Y, мм</Label>
                <Input
                  type="number"
                  step="0.5"
                  value={dy}
                  onChange={(e) => setDy(parseFloat(e.target.value) || 0)}
                  data-testid="cal-dy"
                />
              </div>
            </div>
            <Button variant="outline" className="w-full mt-3" onClick={doTestSheet} data-testid="btn-testsheet">
              <Printer className="h-4 w-4 mr-2" /> Пробный лист выравнивания
            </Button>
            <p className="text-[11px] text-muted-foreground mt-2">
              Распечатайте пробный лист на пустом бланке. Если кресты сместились —
              подвиньте X/Y и повторите.
            </p>
          </div>

          {/* Silent printing — desktop app only */}
          {IS_DESKTOP && (
            <div className="rounded-lg border border-[#E11D48]/40 bg-[#E11D48]/5 p-3 space-y-2" data-testid="silent-print-box">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Printer className="h-4 w-4 text-[#E11D48]" /> Печать на принтер (без окон)
              </div>
              <select
                value={selectedPrinter}
                onChange={(e) => setSelectedPrinter(e.target.value)}
                data-testid="printer-select"
                className="w-full rounded-md bg-white/10 border border-white/15 px-3 py-2 text-sm outline-none focus:border-[#E11D48]"
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
                className="w-full bg-[#E11D48] hover:bg-[#BE123C]"
                data-testid="btn-print-silent"
              >
                <Printer className="h-4 w-4 mr-2" />
                {printing ? "Печать…" : "Печать на бланк (тихо, 100%)"}
              </Button>
              <p className="text-[11px] text-white/50 leading-snug">
                Печатает сразу на выбранный принтер, в фактическом размере (147×103 мм),
                без окна выбора формата. Вставьте бланк в принтер и нажмите.
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="grid grid-cols-2 gap-2">
            <Button onClick={doPreview} className="bg-[#E11D48] hover:bg-[#BE123C]" data-testid="btn-preview">
              <Eye className="h-4 w-4 mr-2" /> Предпросмотр
            </Button>
            <Button onClick={doPrint} variant="outline" data-testid="btn-print">
              <Printer className="h-4 w-4 mr-2" /> Печать (PDF)
            </Button>
            <Button onClick={doDownload} variant="outline" data-testid="btn-download">
              <Download className="h-4 w-4 mr-2" /> Скачать PDF
            </Button>
            <Button onClick={doSave} variant="outline" data-testid="btn-save">
              <Save className="h-4 w-4 mr-2" /> Сохранить
            </Button>
            <Button onClick={resetLayout} variant="ghost" className="col-span-2">
              <RotateCcw className="h-4 w-4 mr-2" /> Сбросить раскладку
            </Button>
          </div>

          {/* Fields inputs */}
          <div className="rounded-lg border border-white/10 bg-white/5 p-4 space-y-4 max-h-[520px] overflow-auto">
            {Object.entries(groups).map(([g, fs]) => (
              <div key={g}>
                <div className="text-xs uppercase tracking-wider text-[#E11D48] font-semibold mb-2">{g}</div>
                <div className="space-y-2">
                  {fs.map((f) => (
                    <div key={f.key}>
                      <Label className="text-[11px] text-muted-foreground">{f.label}</Label>
                      <Input
                        value={values[f.key] || ""}
                        onFocus={() => setSelected(f.key)}
                        onChange={(e) => setVal(f.key, e.target.value)}
                        className="h-8 text-sm"
                        data-testid={`input-${f.key}`}
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Preview dialog */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Предпросмотр (данные поверх бланка)</DialogTitle>
          </DialogHeader>
          {previewUrl && (
            <iframe title="overlay-preview" src={previewUrl} className="w-full h-[70vh] rounded-md bg-white" />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
