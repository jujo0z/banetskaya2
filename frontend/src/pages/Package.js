import React, { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  ClipboardList,
  Printer,
  Download,
  Upload,
  FileSignature,
  Stamp,
  Users,
} from "lucide-react";
import {
  downloadMasterTemplate,
  masterUpload,
  openPackagePdf,
  downloadPackagePdf,
} from "@/lib/apiClient";

const DOC_TOGGLES = [
  { key: "contract", label: "Договор найма", icon: FileSignature },
  { key: "forma19", label: "Форма 19", icon: ClipboardList },
  { key: "forma24", label: "Форма 24", icon: ClipboardList },
  { key: "soobshenie", label: "Сообщение", icon: Stamp },
  { key: "zayavlenie", label: "Заявление о регистрации", icon: FileSignature },
];

export default function Package() {
  const [people, setPeople] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [duplexFlip, setDuplexFlip] = useState("long");
  const [include, setInclude] = useState({
    contract: true,
    forma19: true,
    forma24: true,
    soobshenie: true,
    zayavlenie: true,
  });
  const fileRef = React.useRef(null);

  const onDownloadTemplate = async () => {
    try {
      await downloadMasterTemplate();
      toast.success("Шаблон Excel скачан");
    } catch {
      toast.error("Не удалось скачать шаблон");
    }
  };

  const onUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const data = await masterUpload(file);
      setPeople(data.master || []);
      toast.success(`Загружено человек: ${data.count}`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Ошибка загрузки Excel");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const toggle = (key) => setInclude((s) => ({ ...s, [key]: !s[key] }));

  const anyDoc = Object.values(include).some(Boolean);

  const run = async (mode) => {
    if (!people.length) {
      toast.error("Сначала загрузите заполненный Excel-шаблон");
      return;
    }
    if (!anyDoc) {
      toast.error("Выберите хотя бы один документ");
      return;
    }
    setBusy(true);
    try {
      if (mode === "download") await downloadPackagePdf(people, duplexFlip, include);
      else await openPackagePdf(people, duplexFlip, include);
      toast.success("Пакет сформирован");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Ошибка формирования пакета");
    } finally {
      setBusy(false);
    }
  };

  const personLabel = (p, i) => (p?.fio || "").toString().trim() || `Запись ${i + 1}`;

  return (
    <div className="space-y-8" data-testid="package-page">
      {/* header */}
      <div>
        <div className="flex items-center gap-3">
          <div className="h-11 w-11 rounded-xl bg-gradient-to-br from-[#F43F5E] to-[#BE123C] flex items-center justify-center glow-crimson">
            <Printer className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="font-heading text-3xl font-bold tracking-tight">Полный пакет документов</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Один PDF по каждому человеку: договор, лист «Форма 19 + Форма 24» (по 2 копии) и лист «Сообщение».
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: data */}
        <div className="lg:col-span-2 space-y-6">
          {/* Step 1 — Excel */}
          <div className="glass rounded-2xl border border-white/10 p-6 space-y-4">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <span className="h-6 w-6 rounded-full bg-[#E11D48] text-white text-xs flex items-center justify-center">1</span>
              Данные из Excel-шаблона
            </div>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.xlsm"
              onChange={onUpload}
              className="hidden"
              data-testid="package-file-input"
            />
            <div className="flex flex-wrap gap-2">
              <Button
                onClick={() => fileRef.current?.click()}
                disabled={uploading}
                className="bg-[#E11D48] hover:bg-[#be123c] text-white"
                data-testid="package-upload-btn"
              >
                <Upload className="h-4 w-4 mr-2" />
                {uploading ? "Загрузка…" : "Загрузить заполненный Excel"}
              </Button>
              <Button onClick={onDownloadTemplate} variant="outline" data-testid="package-template-btn">
                <Download className="h-4 w-4 mr-2" />
                Скачать пустой шаблон
              </Button>
            </div>
            <p className="text-[11px] text-muted-foreground">
              Одна строка = один человек = все его документы. Первая строка шаблона уже заполнена примером —
              можно скачать, посмотреть формат и заполнить своими данными.
            </p>
          </div>

          {/* Loaded people */}
          <div className="glass rounded-2xl border border-white/10 p-6">
            <div className="flex items-center gap-2 text-sm font-semibold mb-3">
              <Users className="h-4 w-4 text-[#E11D48]" />
              Загружено людей: {people.length}
            </div>
            {people.length === 0 ? (
              <p className="text-sm text-muted-foreground">Пока пусто — загрузите Excel-файл выше.</p>
            ) : (
              <div className="flex flex-wrap gap-2" data-testid="package-people-list">
                {people.map((p, i) => (
                  <span
                    key={i}
                    className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-sm"
                  >
                    {personLabel(p, i)}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: options + actions */}
        <div className="space-y-6">
          {/* Step 2 — documents */}
          <div className="glass rounded-2xl border border-white/10 p-6 space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <span className="h-6 w-6 rounded-full bg-[#E11D48] text-white text-xs flex items-center justify-center">2</span>
              Что включить в пакет
            </div>
            <div className="space-y-2">
              {DOC_TOGGLES.map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => toggle(key)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl border text-sm transition-all ${
                    include[key]
                      ? "border-[#E11D48] bg-[#E11D48]/10 text-white"
                      : "border-white/10 text-muted-foreground hover:border-white/30"
                  }`}
                  data-testid={`package-toggle-${key}`}
                >
                  <span
                    className={`h-4 w-4 rounded flex items-center justify-center text-[10px] ${
                      include[key] ? "bg-[#E11D48] text-white" : "bg-white/10"
                    }`}
                  >
                    {include[key] ? "✓" : ""}
                  </span>
                  <Icon className="h-4 w-4" />
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Duplex */}
          <div className="glass rounded-2xl border border-white/10 p-6 space-y-3">
            <div className="text-sm font-semibold">Двусторонняя печать</div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setDuplexFlip("long")}
                className={`px-3 py-2 rounded-lg border text-xs transition-all ${
                  duplexFlip === "long" ? "border-[#E11D48] bg-[#E11D48]/10 text-white" : "border-white/10 text-muted-foreground"
                }`}
                data-testid="package-duplex-long"
              >
                По длинному краю
              </button>
              <button
                type="button"
                onClick={() => setDuplexFlip("short")}
                className={`px-3 py-2 rounded-lg border text-xs transition-all ${
                  duplexFlip === "short" ? "border-[#E11D48] bg-[#E11D48]/10 text-white" : "border-white/10 text-muted-foreground"
                }`}
                data-testid="package-duplex-short"
              >
                По короткому краю
              </button>
            </div>
          </div>

          {/* Step 3 — actions */}
          <div className="glass rounded-2xl border border-[#E11D48]/30 p-6 space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <span className="h-6 w-6 rounded-full bg-[#E11D48] text-white text-xs flex items-center justify-center">3</span>
              Печать / сохранение
            </div>
            <Button
              onClick={() => run("open")}
              disabled={busy || !people.length}
              className="w-full bg-[#E11D48] hover:bg-[#be123c] text-white"
              data-testid="package-print-btn"
            >
              <Printer className="h-4 w-4 mr-2" />
              {busy ? "Формирование…" : "Открыть для печати"}
            </Button>
            <Button
              onClick={() => run("download")}
              disabled={busy || !people.length}
              variant="outline"
              className="w-full"
              data-testid="package-save-btn"
            >
              <Download className="h-4 w-4 mr-2" />
              Скачать PDF
            </Button>
            <p className="text-[11px] text-muted-foreground">
              «Открыть для печати» откроет готовый PDF в новой вкладке — нажмите Ctrl+P (⌘+P) и печатайте.
              Для двусторонней печати выберите в диалоге принтера «двусторонняя».
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
