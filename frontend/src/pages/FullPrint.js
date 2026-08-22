import React, { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Printer, Download, Shuffle, Eraser, FileText } from "lucide-react";
import {
  getOverlayLayout,
  openOverlayPdf,
  downloadOverlayPdf,
  getPrinters,
  printOverlaySilent,
} from "@/lib/apiClient";
import { IS_DESKTOP } from "@/lib/env";
import { randomRecord } from "@/pages/BlankOverlay";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const BG_URL = `${BACKEND_URL}/api/overlay/form-background`;
const PAGE_W_PT = (147 / 25.4) * 72; // ~416.69

// Full print always renders the scanned blank as background + data, sized 147x103 mm.
export default function FullPrint() {
  const [layout, setLayout] = useState([]);
  const [values, setValues] = useState({});
  const [dx, setDx] = useState(0);
  const [dy, setDy] = useState(0);
  const [loading, setLoading] = useState(true);
  const [cw, setCw] = useState(700);
  // desktop silent printing
  const [printers, setPrinters] = useState([]);
  const [selectedPrinter, setSelectedPrinter] = useState("");
  const [printing, setPrinting] = useState(false);

  const canvasRef = useRef(null);

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

  const scale = cw / PAGE_W_PT;
  const setVal = (k, v) => setValues((s) => ({ ...s, [k]: v }));

  const fillRandom = () => {
    setValues(randomRecord());
    toast.success("Заполнено случайными данными");
  };
  const clearAll = () => {
    setValues({});
    toast("Поля очищены");
  };

  const opts = () => ({ layout, dx_mm: dx, dy_mm: dy, pageSize: "card", withForm: true });

  const doOpen = async () => {
    try {
      await openOverlayPdf([values], opts());
      toast("PDF открыт в новой вкладке — печатайте «Фактический размер» (100%)");
    } catch (e) {
      toast.error("Ошибка открытия PDF");
    }
  };
  const doDownload = async () => {
    try {
      await downloadOverlayPdf([values], opts());
    } catch (e) {
      toast.error("Ошибка скачивания");
    }
  };
  const doPrintSilent = async () => {
    setPrinting(true);
    try {
      const res = await printOverlaySilent([values], { ...opts(), printerName: selectedPrinter });
      toast.success(`Отправлено на печать: ${res.printer}`);
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
    <div className="p-6 lg:p-8 space-y-6">
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight flex items-center gap-3">
          <FileText className="h-8 w-8 text-[#E11D48]" /> Полная печать
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Печать всего документа на обычном белом листе: бланк набирается заново (чистый типографский вид) + данные.
          Размер 147×103 мм. Готовый бумажный бланк не нужен.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_360px] gap-6">
        {/* ---- Live preview (read-only) ---- */}
        <div>
          <div
            ref={canvasRef}
            className="relative w-full rounded-lg overflow-hidden border border-white/10 shadow-2xl select-none bg-white"
            style={{ aspectRatio: "147 / 103" }}
            data-testid="fullprint-canvas"
          >
            <img
              src={BG_URL}
              alt="Бланк"
              className="absolute inset-0 w-full h-full object-fill pointer-events-none"
              draggable={false}
            />
            {layout.map((f) => {
              const v = values[f.key];
              const fontPx = Math.max(7, (f.font_pt || 9) * scale);
              return (
                <div
                  key={f.key}
                  className="absolute whitespace-nowrap leading-none px-0.5"
                  style={{
                    left: `${f.x_pct}%`,
                    top: `${f.y_pct}%`,
                    fontSize: `${fontPx}px`,
                    color: "#0a0a1f",
                    transform: "translate(0, -0.9em)",
                    fontFamily: "Arial, sans-serif",
                  }}
                  title={f.label}
                >
                  {v || ""}
                </div>
              );
            })}
          </div>
          <p className="text-[11px] text-white/50 mt-2">
            Так документ и напечатается на белом листе. Позиции полей — из раскладки раздела «Печать на бланке».
          </p>
        </div>

        {/* ---- Controls ---- */}
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-2">
            <Button onClick={fillRandom} variant="outline" data-testid="btn-random">
              <Shuffle className="h-4 w-4 mr-2" /> Случайные
            </Button>
            <Button onClick={clearAll} variant="ghost" data-testid="btn-clear">
              <Eraser className="h-4 w-4 mr-2" /> Очистить
            </Button>
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
                {printing ? "Печать…" : "Печать документа (тихо, 100%)"}
              </Button>
            </div>
          )}

          <div className="grid grid-cols-2 gap-2">
            <Button onClick={doOpen} className="bg-[#E11D48] hover:bg-[#BE123C]" data-testid="btn-open">
              <Printer className="h-4 w-4 mr-2" /> Открыть/Печать PDF
            </Button>
            <Button onClick={doDownload} variant="outline" data-testid="btn-download">
              <Download className="h-4 w-4 mr-2" /> Скачать PDF
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
    </div>
  );
}
