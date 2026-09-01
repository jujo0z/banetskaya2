import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { useLocation } from "react-router-dom";
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
  RotateCw,
  Download,
  Info,
  Lock,
  Unlock,
  Trash2,
  Copy,
  Pencil,
  FolderPlus,
} from "lucide-react";
import {
  getOverlayLayout,
  overlayPdfUrl,
  openOverlayPdf,
  downloadOverlayPdf,
  openOverlayTestSheet,
  openCarrierFrame,
  getPrinters,
  printOverlaySilent,
  getRegProfile,
  listOverlayProfiles,
  createOverlayProfile,
  updateOverlayProfile,
  deleteOverlayProfile,
  setActiveOverlayProfile,
} from "@/lib/apiClient";
import { IS_DESKTOP } from "@/lib/env";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const BG_URL = `${BACKEND_URL}/api/overlay/background`;
// Флаг: раздел «Печать на бланке» временно отключён (в доработке).
// Чтобы вернуть — поставьте false. Весь код раздела ниже сохранён.
const OVERLAY_FEATURE_DISABLED = true;
// Обязательные поля бланка «СООБЩЕНИЕ» (проверяются перед печатью).
export const REQUIRED_KEYS = [
  "fio", "address",
  "from_day", "from_month", "from_year",
  "to_day", "to_month", "to_year",
];
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
  const [profiles, setProfiles] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [layout, setLayout] = useState([]);
  const [values, setValues] = useState({});
  const [locked, setLocked] = useState(new Set()); // ключи «постоянных» (замок) полей
  const [dx, setDx] = useState(0);
  const [dy, setDy] = useState(0);
  const [rotate, setRotate] = useState(0);
  const [pageSize, setPageSize] = useState("card");
  const [a4Position, setA4Position] = useState("top-left");
  const [selected, setSelected] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [cw, setCw] = useState(700);
  // Silent printing (desktop app only)
  const [printers, setPrinters] = useState([]);
  const [selectedPrinter, setSelectedPrinter] = useState("");
  const [printing, setPrinting] = useState(false);
  const [missing, setMissing] = useState(new Set());

  const location = useLocation();
  const canvasRef = useRef(null);
  const dragRef = useRef(null);

  const activeProfile = profiles.find((p) => p.id === activeId) || null;

  // ---- initial load: profiles + reg-profile + history prefill ----
  useEffect(() => {
    (async () => {
      const prefill = location.state?.prefill || null;
      let data;
      try {
        data = await listOverlayProfiles();
      } catch (e) {
        toast.error("Не удалось загрузить профили");
        setLoading(false);
        return;
      }
      const list = data.profiles || [];
      const act = list.find((p) => p.id === data.active_id) || list[0] || null;
      const consts = (act && act.constants) || {};
      const base = {};
      const lockedSet = new Set();
      Object.entries(consts).forEach(([k, c]) => {
        base[k] = (c && c.value) || "";
        if (c && c.locked) lockedSet.add(k);
      });
      try {
        const rp = await getRegProfile();
        if (rp?.reg_organ && !base.reg_organ) base.reg_organ = rp.reg_organ;
        if (rp?.chief && !base.chief) base.chief = rp.chief;
      } catch (e) {
        /* ignore */
      }
      if (prefill) Object.assign(base, prefill);
      setProfiles(list);
      setActiveId(act ? act.id : null);
      setLayout((act && act.layout) || []);
      setDx((act && act.dx_mm) || 0);
      setDy((act && act.dy_mm) || 0);
      setRotate((act && act.rotate) || 0);
      setLocked(lockedSet);
      setValues(base);
      setLoading(false);
      if (prefill) toast.success("Данные договора подставлены в бланк");
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
        /* printing UI simply won't appear if this fails */
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

  const scale = cw / PAGE_W_PT; // px per pt on screen

  const setVal = (k, v) => {
    setValues((s) => ({ ...s, [k]: v }));
    if (v && v.trim()) {
      setMissing((m) => {
        if (!m.has(k)) return m;
        const n = new Set(m);
        n.delete(k);
        return n;
      });
    }
  };

  const checkRequired = () => {
    const miss = new Set(
      REQUIRED_KEYS.filter((k) => layout.some((f) => f.key === k) && !((values[k] || "").toString().trim()))
    );
    setMissing(miss);
    if (miss.size > 0) {
      toast.error(`Заполните обязательные поля (${miss.size}) — подсвечены красным`);
      return false;
    }
    return true;
  };

  const fillRandom = () => {
    // random data, but keep locked (constant) values intact
    const r = randomRecord();
    setValues((prev) => {
      const next = { ...r };
      locked.forEach((k) => { next[k] = prev[k]; });
      return next;
    });
    toast.success("Заполнено случайными данными");
  };
  const clearAll = () => {
    setValues((prev) => {
      const next = {};
      locked.forEach((k) => { next[k] = prev[k]; });
      return next;
    });
    toast("Поля очищены (постоянные сохранены)");
  };

  // ---- build the constants map for saving ----
  const buildConstants = useCallback(() => {
    const c = {};
    locked.forEach((k) => {
      c[k] = { value: values[k] || "", locked: true };
    });
    return c;
  }, [locked, values]);

  // ---- profiles ----
  const applyProfile = (p) => {
    setActiveId(p.id);
    setLayout(p.layout || []);
    setDx(p.dx_mm || 0);
    setDy(p.dy_mm || 0);
    setRotate(p.rotate || 0);
    const consts = p.constants || {};
    const base = {};
    const lockedSet = new Set();
    Object.entries(consts).forEach(([k, c]) => {
      base[k] = (c && c.value) || "";
      if (c && c.locked) lockedSet.add(k);
    });
    setLocked(lockedSet);
    setValues(base);
    setSelected(null);
    setMissing(new Set());
  };

  const switchProfile = async (id) => {
    const p = profiles.find((x) => x.id === id);
    if (!p) return;
    applyProfile(p);
    try {
      await setActiveOverlayProfile(id);
    } catch (e) {
      /* non-critical */
    }
  };

  const createProfile = async () => {
    const name = window.prompt("Название нового профиля:", `Профиль ${profiles.length + 1}`);
    if (!name) return;
    try {
      const p = await createOverlayProfile({ name });
      setProfiles((ps) => [...ps, p]);
      applyProfile(p);
      toast.success(`Профиль «${p.name}» создан`);
    } catch (e) {
      toast.error("Не удалось создать профиль");
    }
  };

  const duplicateProfile = async () => {
    if (!activeProfile) return;
    const name = window.prompt("Название копии:", `${activeProfile.name} (копия)`);
    if (!name) return;
    try {
      const p = await createOverlayProfile({
        name, layout, dx_mm: dx, dy_mm: dy, rotate, constants: buildConstants(),
      });
      setProfiles((ps) => [...ps, p]);
      applyProfile(p);
      toast.success("Профиль продублирован");
    } catch (e) {
      toast.error("Не удалось продублировать");
    }
  };

  const renameProfile = async () => {
    if (!activeProfile) return;
    const name = window.prompt("Новое название профиля:", activeProfile.name);
    if (!name) return;
    try {
      const p = await updateOverlayProfile(activeId, {
        name, layout, dx_mm: dx, dy_mm: dy, rotate, constants: buildConstants(),
      });
      setProfiles((ps) => ps.map((x) => (x.id === activeId ? p : x)));
      toast.success("Профиль переименован");
    } catch (e) {
      toast.error("Не удалось переименовать");
    }
  };

  const removeProfile = async () => {
    if (!activeProfile) return;
    if (profiles.length <= 1) {
      toast.error("Нельзя удалить последний профиль");
      return;
    }
    if (!window.confirm(`Удалить профиль «${activeProfile.name}»?`)) return;
    try {
      await deleteOverlayProfile(activeId);
      const data = await listOverlayProfiles();
      const list = data.profiles || [];
      setProfiles(list);
      const act = list.find((p) => p.id === data.active_id) || list[0];
      if (act) applyProfile(act);
      toast.success("Профиль удалён");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Не удалось удалить");
    }
  };

  const saveProfile = async () => {
    if (!activeProfile) return;
    try {
      const p = await updateOverlayProfile(activeId, {
        name: activeProfile.name, layout, dx_mm: dx, dy_mm: dy, rotate, constants: buildConstants(),
      });
      setProfiles((ps) => ps.map((x) => (x.id === activeId ? p : x)));
      toast.success(`Профиль «${p.name}» сохранён`);
    } catch (e) {
      toast.error("Не удалось сохранить профиль");
    }
  };

  // ---- fields: add / remove / lock (constant) ----
  const addField = () => {
    const label = window.prompt("Название нового поля (например: «Особые отметки»):", "");
    if (!label) return;
    const def = window.prompt("Текст по умолчанию (можно оставить пустым):", "") || "";
    const key = "custom_" + Math.random().toString(36).slice(2, 8);
    setLayout((l) => [...l, { key, label, x_pct: 45, y_pct: 45, font_pt: 9, group: "Свои поля", custom: true }]);
    setValues((v) => ({ ...v, [key]: def }));
    setSelected(key);
    toast.success("Поле добавлено — перетащите его на нужное место");
  };

  const removeField = (key) => {
    const f = layout.find((x) => x.key === key);
    if (!f) return;
    if (!window.confirm(`Убрать поле «${f.label}» из этого профиля?`)) return;
    setLayout((l) => l.filter((x) => x.key !== key));
    setValues((v) => { const n = { ...v }; delete n[key]; return n; });
    setLocked((s) => { const n = new Set(s); n.delete(key); return n; });
    if (selected === key) setSelected(null);
  };

  const toggleConstant = (key) => {
    setLocked((s) => {
      const n = new Set(s);
      if (n.has(key)) n.delete(key);
      else n.add(key);
      return n;
    });
  };

  const restoreDefaults = async () => {
    if (!window.confirm("Вернуть стандартный набор полей? Ваши свои поля будут убраны.")) return;
    try {
      const data = await getOverlayLayout();
      setLayout(data.layout || []);
      toast("Стандартная раскладка полей восстановлена (не забудьте «Сохранить»)");
    } catch (e) {
      toast.error("Ошибка");
    }
  };

  // ---- dragging ----
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
  const onPointerDown = (e, key) => {
    e.preventDefault();
    e.stopPropagation();
    setSelected(key);
    dragRef.current = { key };
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
  };

  const changeFont = (key, delta) =>
    setLayout((prev) => prev.map((f) => (f.key === key ? { ...f, font_pt: Math.max(5, Math.min(20, (f.font_pt || 9) + delta)) } : f)));

  // ---- print actions ----
  const doPreview = async () => {
    try {
      const url = await overlayPdfUrl([values], { layout, dx_mm: dx, dy_mm: dy, pageSize, rotate, a4Position, withBackground: true });
      setPreviewUrl(url);
      setPreviewOpen(true);
    } catch (e) {
      toast.error("Ошибка предпросмотра");
    }
  };
  const doPrint = async () => {
    if (!checkRequired()) return;
    try {
      await openOverlayPdf([values], { layout, dx_mm: dx, dy_mm: dy, pageSize, rotate, a4Position });
      toast("PDF открыт в новой вкладке — печатайте «Фактический размер» (100%)");
    } catch (e) {
      toast.error("Ошибка печати");
    }
  };
  const doPrintSilent = async () => {
    if (!checkRequired()) return;
    setPrinting(true);
    try {
      const res = await printOverlaySilent([values], {
        layout, dx_mm: dx, dy_mm: dy, pageSize, rotate, a4Position, printerName: selectedPrinter,
      });
      toast.success(
        pageSize === "a4"
          ? `Отправлено на печать (лист A4, бланк в углу): ${res.printer}`
          : `Отправлено на печать (147×103 мм): ${res.printer}`
      );
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Ошибка печати");
    } finally {
      setPrinting(false);
    }
  };
  const doDownload = async () => {
    try {
      await downloadOverlayPdf([values], { layout, dx_mm: dx, dy_mm: dy, pageSize, rotate, a4Position });
    } catch (e) {
      toast.error("Ошибка скачивания");
    }
  };
  const doTestSheet = async () => {
    try {
      await openOverlayTestSheet(dx, dy, pageSize, rotate);
      toast("Пробный лист открыт — печатайте с масштабом 100%");
    } catch (e) {
      toast.error("Ошибка пробного листа");
    }
  };
  const doCarrierFrame = async () => {
    try {
      await openCarrierFrame(a4Position);
      toast("Рамка-держатель открыта — печатайте A4 в масштабе 100%");
    } catch (e) {
      toast.error("Ошибка печати рамки");
    }
  };

  if (OVERLAY_FEATURE_DISABLED) {
    return (
      <div data-testid="blank-overlay-page">
        <div className="mb-6">
          <h1 className="font-heading text-4xl font-bold flex items-center gap-3">
            <Stamp className="h-8 w-8 text-[#EC4899]" /> Печать на бланке
          </h1>
        </div>
        <div
          className="rounded-2xl border border-pink-100 bg-white/80 p-10 text-center max-w-2xl mx-auto mt-10"
          data-testid="overlay-disabled-stub"
        >
          <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-full bg-[#EC4899]/10">
            <Stamp className="h-8 w-8 text-[#EC4899]" />
          </div>
          <h2 className="text-2xl font-bold mb-3">Раздел временно недоступен</h2>
          <p className="text-muted-foreground leading-relaxed">
            Печать данных поверх готового бланка сейчас в доработке — мы улучшаем точность
            попадания на линии бланка. Пока раздел отключён.
          </p>
          <p className="text-muted-foreground leading-relaxed mt-3">
            Остальные функции работают как обычно: договоры найма, история, экспорт DOCX/PDF.
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return <div className="text-muted-foreground">Загрузка редактора…</div>;
  }

  const selField = layout.find((f) => f.key === selected);

  return (
    <div data-testid="blank-overlay-page">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="font-heading text-4xl font-bold flex items-center gap-3">
            <Stamp className="h-8 w-8 text-[#EC4899]" /> Печать на бланке
          </h1>
          <p className="text-muted-foreground mt-2 max-w-2xl">
            Бланк «СООБЩЕНИЕ» (147×103&nbsp;мм). Данные печатаются поверх готового бланка.
            Настройте размещение полей и сохраните его в профиль (свой под каждый принтер/бланк).
          </p>
        </div>
        <div className="flex flex-wrap gap-2 justify-end">
          <Button variant="outline" onClick={fillRandom} data-testid="btn-random">
            <Shuffle className="h-4 w-4 mr-2" /> Случайные данные
          </Button>
          <Button variant="outline" onClick={clearAll}>Очистить</Button>
        </div>
      </div>

      {/* Profile bar */}
      <div className="mb-6 rounded-lg border border-[#EC4899]/30 bg-[#EC4899]/5 p-3 flex flex-wrap items-center gap-2" data-testid="profile-bar">
        <span className="text-sm font-semibold mr-1">Профиль размещения:</span>
        <select
          value={activeId || ""}
          onChange={(e) => switchProfile(e.target.value)}
          data-testid="profile-select"
          className="rounded-md bg-white border border-pink-200 px-3 py-2 text-sm outline-none focus:border-[#EC4899] min-w-[180px]"
        >
          {profiles.map((p) => (
            <option key={p.id} value={p.id} className="bg-neutral-900">{p.name}</option>
          ))}
        </select>
        <Button size="sm" onClick={saveProfile} className="bg-[#EC4899] hover:bg-[#DB2777]" data-testid="btn-save-profile">
          <Save className="h-4 w-4 mr-1" /> Сохранить
        </Button>
        <Button size="sm" variant="outline" onClick={createProfile} data-testid="btn-create-profile">
          <FolderPlus className="h-4 w-4 mr-1" /> Новый
        </Button>
        <Button size="sm" variant="outline" onClick={duplicateProfile} data-testid="btn-dup-profile">
          <Copy className="h-4 w-4 mr-1" /> Дублировать
        </Button>
        <Button size="sm" variant="outline" onClick={renameProfile}>
          <Pencil className="h-4 w-4 mr-1" /> Переименовать
        </Button>
        <Button size="sm" variant="ghost" onClick={removeProfile} className="text-[#EC4899] hover:bg-[#EC4899]/10" data-testid="btn-del-profile">
          <Trash2 className="h-4 w-4 mr-1" /> Удалить
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_360px] gap-6">
        {/* ---- Canvas ---- */}
        <div>
          <div
            ref={canvasRef}
            className="relative w-full rounded-lg overflow-hidden border border-pink-100 shadow-2xl select-none bg-white"
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
              const isLocked = locked.has(f.key);
              const fontPx = Math.max(7, (f.font_pt || 9) * scale);
              return (
                <div
                  key={f.key}
                  onPointerDown={(e) => onPointerDown(e, f.key)}
                  className={`absolute cursor-move whitespace-nowrap leading-none px-0.5 rounded-sm transition-shadow ${
                    isSel ? "ring-2 ring-[#EC4899] bg-[#EC4899]/10" : "hover:ring-1 hover:ring-[#EC4899]/50"
                  }`}
                  style={{
                    left: `${f.x_pct}%`,
                    top: `${f.y_pct}%`,
                    fontSize: `${fontPx}px`,
                    color: v ? (isLocked ? "#0369a1" : "#0a0a1f") : "#c026a1",
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
            Розовым — пустые поля (их подписи), при печати не выводятся. Синим — постоянные (с замком).
            Тяните любое поле, чтобы поставить его точно на нужную строку.
          </p>
        </div>

        {/* ---- Side panel ---- */}
        <div className="space-y-5">
          {/* Selected field tools */}
          {selField && (
            <div className="rounded-lg border border-[#EC4899]/40 bg-[#EC4899]/5 p-4">
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
              <div className="flex gap-2 mt-3">
                <Button
                  size="sm"
                  variant="outline"
                  className={locked.has(selField.key) ? "border-sky-500 text-sky-400" : ""}
                  onClick={() => toggleConstant(selField.key)}
                  data-testid={`toggle-const-${selField.key}`}
                >
                  {locked.has(selField.key) ? <Lock className="h-4 w-4 mr-1" /> : <Unlock className="h-4 w-4 mr-1" />}
                  {locked.has(selField.key) ? "Постоянное" : "Сделать постоянным"}
                </Button>
                <Button size="sm" variant="ghost" className="text-[#EC4899] hover:bg-[#EC4899]/10" onClick={() => removeField(selField.key)} data-testid={`remove-field-${selField.key}`}>
                  <Trash2 className="h-4 w-4 mr-1" /> Убрать
                </Button>
              </div>
            </div>
          )}

          {/* Paper size */}
          <div className="rounded-lg border border-pink-100 bg-white/80 p-4">
            <div className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Printer className="h-4 w-4 text-[#EC4899]" /> Размер листа для печати
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setPageSize("card")}
                className={`rounded-md border px-3 py-2 text-sm text-left transition ${
                  pageSize === "card" ? "border-[#EC4899] bg-[#EC4899]/10" : "border-pink-100 hover:border-pink-200"
                }`}
                data-testid="paper-card"
              >
                <div className="font-semibold">147×103 мм</div>
                <div className="text-[11px] text-muted-foreground">если принтер умеет малый формат / A6</div>
              </button>
              <button
                type="button"
                onClick={() => setPageSize("a4")}
                className={`rounded-md border px-3 py-2 text-sm text-left transition ${
                  pageSize === "a4" ? "border-[#EC4899] bg-[#EC4899]/10" : "border-pink-100 hover:border-pink-200"
                }`}
                data-testid="paper-a4"
              >
                <div className="font-semibold">Лист A4</div>
                <div className="text-[11px] text-muted-foreground">для обычных A4-принтеров · рекомендуется</div>
              </button>
            </div>
            {pageSize === "a4" ? (
              <>
                <div className="mt-3 flex gap-2 text-[11px] text-muted-foreground bg-emerald-500/10 border border-emerald-500/20 rounded-md p-2">
                  <Info className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span>
                    Ваш принтер печатает только A4? Это нормально. Данные лягут в выбранный угол листа
                    в реальном размере <b>147×103&nbsp;мм</b> и НЕ растянутся. Положите готовый бланк в{" "}
                    <b>тот&nbsp;же угол</b> листа A4 и печатайте <b>в 100%</b> (без «по размеру страницы» / «вписать»).
                  </span>
                </div>
                <div className="mt-3">
                  <div className="text-xs font-semibold mb-2">Где на листе A4 лежит бланк</div>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { key: "top-left", label: "Сверху слева" },
                      { key: "top-center", label: "Сверху по центру" },
                      { key: "top-right", label: "Сверху справа" },
                      { key: "center", label: "По центру листа" },
                    ].map((p) => (
                      <button
                        key={p.key}
                        type="button"
                        onClick={() => setA4Position(p.key)}
                        className={`rounded-md border px-3 py-2 text-sm text-left transition ${
                          a4Position === p.key ? "border-[#EC4899] bg-[#EC4899]/10 font-semibold" : "border-pink-100 hover:border-pink-200"
                        }`}
                        data-testid={`a4pos-${p.key}`}
                      >
                        {p.label}
                      </button>
                    ))}
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-2">
                    Совет: у большинства принтеров ручной лоток прижимает бумагу к левому краю — тогда
                    подходит <b>«Сверху слева»</b>. Если бумага центрируется — <b>«Сверху по центру»</b>.
                    Проверьте «Пробным листом» и при небольшом сдвиге подправьте ползунками ниже.
                  </p>

                  <div className="mt-3 rounded-md border border-[#EC4899]/30 bg-[#EC4899]/5 p-3">
                    <div className="text-xs font-semibold mb-1">Бланк «гуляет» по листу? Сделайте держатель</div>
                    <p className="text-[11px] text-muted-foreground mb-2">
                      Напечатайте рамку на A4, наклейте бланк точно по уголкам скотчем — и печатайте данные
                      на этот же лист. Бланк всегда в одном месте, смещений не будет.
                    </p>
                    <Button variant="outline" size="sm" className="w-full" onClick={doCarrierFrame} data-testid="btn-carrier-frame">
                      <Printer className="h-4 w-4 mr-2" /> Печать рамки-держателя (A4, 100%)
                    </Button>
                  </div>
                </div>
              </>
            ) : (
              <div className="mt-3 flex gap-2 text-[11px] text-muted-foreground bg-amber-500/10 border border-amber-500/20 rounded-md p-2">
                <Info className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
                <span>
                  Этот режим подойдёт, только если принтер умеет малый формат: в драйвере задайте
                  размер <b>147×103&nbsp;мм</b> (или A6), печать через <b>обходной/ручной лоток</b>,
                  масштаб <b>100%</b>. Обычные A4-принтеры растянут страницу — тогда выберите «Лист&nbsp;A4».
                </span>
              </div>
            )}
          </div>

          {/* Rotation */}
          <div className="rounded-lg border border-pink-100 bg-white/80 p-4">
            <div className="text-sm font-semibold mb-1 flex items-center gap-2">
              <RotateCw className="h-4 w-4 text-[#EC4899]" /> Поворот под подачу бланка
            </div>
            <p className="text-[11px] text-muted-foreground mb-3">
              Если данные уезжают вбок — меняйте поворот и проверяйте пробным листом. Бланк вертикально
              (узкой стороной вперёд) — обычно нужно <b>90°</b> или <b>270°</b>.
            </p>
            {pageSize === "a4" && (
              <p className="text-[11px] text-amber-400/90 mb-3">
                В режиме «Лист A4» поворот не используется: положите бланк на лист{" "}
                <b>горизонтально</b> (широкой стороной 147&nbsp;мм вдоль верхнего края) в выбранный угол.
              </p>
            )}
            <div className="grid grid-cols-4 gap-2">
              {[0, 90, 180, 270].map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setRotate(r)}
                  className={`rounded-md border px-2 py-2 text-sm transition ${
                    rotate === r ? "border-[#EC4899] bg-[#EC4899]/10 font-semibold" : "border-pink-100 hover:border-pink-200"
                  }`}
                  data-testid={`rotate-${r}`}
                >
                  {r}°
                </button>
              ))}
            </div>
          </div>

          {/* Calibration */}
          <div className="rounded-lg border border-pink-100 bg-white/80 p-4">
            <div className="text-sm font-semibold mb-3 flex items-center gap-2">
              <Crosshair className="h-4 w-4 text-[#EC4899]" /> Калибровка принтера
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs">Сдвиг X, мм</Label>
                <Input type="number" step="0.5" value={dx} onChange={(e) => setDx(parseFloat(e.target.value) || 0)} data-testid="cal-dx" />
              </div>
              <div>
                <Label className="text-xs">Сдвиг Y, мм</Label>
                <Input type="number" step="0.5" value={dy} onChange={(e) => setDy(parseFloat(e.target.value) || 0)} data-testid="cal-dy" />
              </div>
            </div>
            <Button variant="outline" className="w-full mt-3" onClick={doTestSheet} data-testid="btn-testsheet">
              <Printer className="h-4 w-4 mr-2" /> Пробный лист выравнивания
            </Button>
          </div>

          {/* Printer setup instructions */}
          <details className="rounded-lg border border-pink-100 bg-white/80 p-4 group" data-testid="printer-howto">
            <summary className="text-sm font-semibold flex items-center gap-2 cursor-pointer list-none">
              <Info className="h-4 w-4 text-[#EC4899]" /> Как настроить принтер (Kyocera / Canon MF)
              <span className="ml-auto text-[11px] text-muted-foreground group-open:hidden">развернуть</span>
            </summary>
            <ol className="mt-3 space-y-2 text-[11px] text-muted-foreground list-decimal pl-4 leading-relaxed">
              <li>Готовый бланк — в <b>обходной (ручной) лоток</b>. Кладите <b>вертикально</b>: узкой стороной (103&nbsp;мм) вперёд, лицом вверх.</li>
              <li>В окне печати → <b>Свойства</b> → размер бумаги <b>A6</b> или нестандартный <b>147×103&nbsp;мм</b>, источник — <b>Обходной лоток</b>.</li>
              <li>Масштаб — <b>«Фактический размер» / 100%</b>.</li>
              <li>Напечатайте <b>пробный лист</b> на одном бланке. Кресты и линейка должны совпасть.</li>
              <li>Оттиск повёрнут — меняйте <b>Поворот</b>; сдвинут — правьте <b>X/Y</b>. Затем <b>«Сохранить»</b> в профиль.</li>
            </ol>
          </details>

          {/* Silent printing — desktop app only */}
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
                {printing ? "Печать…" : "Печать на бланк (тихо, 100%)"}
              </Button>
            </div>
          )}

          {/* Actions */}
          <div className="grid grid-cols-2 gap-2">
            <Button onClick={doPreview} className="bg-[#EC4899] hover:bg-[#DB2777]" data-testid="btn-preview">
              <Eye className="h-4 w-4 mr-2" /> Предпросмотр
            </Button>
            <Button onClick={doPrint} variant="outline" data-testid="btn-print">
              <Printer className="h-4 w-4 mr-2" /> Печать (PDF)
            </Button>
            <Button onClick={doDownload} variant="outline" data-testid="btn-download">
              <Download className="h-4 w-4 mr-2" /> Скачать PDF
            </Button>
            <Button onClick={restoreDefaults} variant="ghost" data-testid="btn-restore-defaults">
              <RotateCcw className="h-4 w-4 mr-2" /> Стандартные поля
            </Button>
          </div>

          {/* Fields inputs */}
          <div className="rounded-lg border border-pink-100 bg-white/80 p-4 space-y-4 max-h-[520px] overflow-auto">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold">Данные и поля</div>
              <Button size="sm" variant="outline" onClick={addField} data-testid="btn-add-field">
                <Plus className="h-4 w-4 mr-1" /> Добавить поле
              </Button>
            </div>
            {Object.entries(groups).map(([g, fs]) => (
              <div key={g}>
                <div className="text-xs uppercase tracking-wider text-[#EC4899] font-semibold mb-2">{g}</div>
                <div className="space-y-2">
                  {fs.map((f) => {
                    const isLocked = locked.has(f.key);
                    return (
                      <div key={f.key}>
                        <div className="flex items-center justify-between">
                          <Label className="text-[11px] text-muted-foreground">
                            {f.label}
                            {REQUIRED_KEYS.includes(f.key) && <span className="text-[#EC4899]"> *</span>}
                          </Label>
                          <button
                            type="button"
                            onClick={() => toggleConstant(f.key)}
                            title={isLocked ? "Постоянное (замок) — нажмите чтобы разблокировать" : "Сделать постоянным"}
                            className={`p-1 rounded ${isLocked ? "text-sky-400" : "text-muted-foreground hover:text-slate-900"}`}
                            data-testid={`lock-${f.key}`}
                          >
                            {isLocked ? <Lock className="h-3.5 w-3.5" /> : <Unlock className="h-3.5 w-3.5" />}
                          </button>
                        </div>
                        <Input
                          value={values[f.key] || ""}
                          disabled={isLocked}
                          onFocus={() => setSelected(f.key)}
                          onChange={(e) => setVal(f.key, e.target.value)}
                          className={`h-8 text-sm ${missing.has(f.key) ? "border-[#EC4899] ring-1 ring-[#EC4899]" : ""} ${isLocked ? "opacity-70 border-sky-500/40" : ""}`}
                          data-testid={`input-${f.key}`}
                        />
                      </div>
                    );
                  })}
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
