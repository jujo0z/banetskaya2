import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Download, FileCheck2, Info, Database, Trash2, Bookmark, Loader2, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import { FIELDS } from "@/lib/fields";
import { downloadSampleTemplate, seedDemo, clearDemo, getPresets, deletePreset } from "@/lib/apiClient";

export default function Settings() {
  const [downloading, setDownloading] = useState(false);
  const [seeding, setSeeding] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [presets, setPresets] = useState([]);

  useEffect(() => {
    getPresets().then(setPresets).catch(() => {});
  }, []);

  async function handleSeed() {
    setSeeding(true);
    try {
      const res = await seedDemo();
      toast.success(res.message || "Демо-данные загружены");
    } catch {
      toast.error("Не удалось загрузить демо-данные");
    } finally {
      setSeeding(false);
    }
  }

  async function handleClearDemo() {
    setClearing(true);
    try {
      const res = await clearDemo();
      toast.success(`Удалено демо-договоров: ${res.deleted}`);
    } catch {
      toast.error("Не удалось очистить демо-данные");
    } finally {
      setClearing(false);
    }
  }

  async function handleDeletePreset(id) {
    try {
      await deletePreset(id);
      setPresets((prev) => prev.filter((p) => p.id !== id));
      toast.success("Пресет удалён");
    } catch {
      toast.error("Не удалось удалить пресет");
    }
  }

  async function handleSample() {
    setDownloading(true);
    try {
      await downloadSampleTemplate();
      toast.success("Шаблон Excel скачан");
    } catch {
      toast.error("Не удалось скачать шаблон");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-heading text-4xl sm:text-5xl font-black tracking-tighter">Настройки</h1>
        <p className="text-muted-foreground mt-2">
          Шаблон договора, поля автозаполнения и образец Excel.
        </p>
      </div>

      {/* Template info */}
      <div className="bg-card border border-border p-6">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 bg-[#E11D48]/10 flex items-center justify-center shrink-0">
            <FileCheck2 className="h-5 w-5 text-[#E11D48]" strokeWidth={2} />
          </div>
          <div className="space-y-2">
            <h2 className="font-heading text-xl font-bold tracking-tight">Шаблон договора</h2>
            <p className="text-sm text-muted-foreground leading-relaxed max-w-2xl">
              Договор найма жилого помещения государственного жилищного фонда в общежитии.
              Оформление, текст, реквизиты колледжа, данные директора и начальника ОКЮР сохраняются
              один в один как в исходном Word. Автоматически подставляются только переменные поля из
              Excel — постоянная часть договора не меняется.
            </p>
            <div className="flex items-center gap-2 text-xs text-muted-foreground bg-accent px-3 py-2 mt-2">
              <Info className="h-4 w-4 shrink-0" />
              Чтобы заменить шаблон на свой, поместите новый .docx с теми же полями — обратитесь к разработчику.
            </div>
          </div>
        </div>
      </div>

      {/* Sample excel */}
      <div className="bg-card border border-border p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="font-heading text-xl font-bold tracking-tight">Образец Excel</h2>
            <p className="text-sm text-muted-foreground mt-1 max-w-xl">
              Скачайте готовый файл с нужными колонками и примером строки — заполните своими данными и
              загрузите на вкладке «Генерация».
            </p>
          </div>
          <Button
            className="rounded-none bg-[#E11D48] hover:bg-[#BE123C] text-white h-11"
            onClick={handleSample}
            disabled={downloading}
            data-testid="settings-download-sample-btn"
          >
            <Download className="h-4 w-4" />
            Скачать шаблон Excel
          </Button>
        </div>
      </div>

      {/* Demo data */}
      <div className="bg-card border border-border p-6" data-testid="settings-demo-card">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 bg-[#E11D48]/10 flex items-center justify-center shrink-0 rounded-md">
            <Database className="h-5 w-5 text-[#E11D48]" strokeWidth={2} />
          </div>
          <div className="flex-1">
            <h2 className="font-heading text-xl font-bold tracking-tight">Тестовые данные</h2>
            <p className="text-sm text-muted-foreground mt-1 max-w-xl">
              Загрузите набор демонстрационных договоров (готовые + черновики), чтобы
              посмотреть, как выглядит история, редактор и печать. Можно очистить в один клик.
            </p>
            <div className="flex flex-wrap gap-2 mt-4">
              <Button
                className="rounded-none bg-[#E11D48] hover:bg-[#BE123C] text-white"
                onClick={handleSeed}
                disabled={seeding}
                data-testid="settings-seed-btn"
              >
                {seeding ? <Loader2 className="h-4 w-4 animate-spin" /> : <Database className="h-4 w-4" />}
                Загрузить демо-договоры
              </Button>
              <Button
                variant="outline"
                className="rounded-none"
                onClick={handleClearDemo}
                disabled={clearing}
                data-testid="settings-clear-demo-btn"
              >
                {clearing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
                Очистить демо
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Presets */}
      <div className="bg-card border border-border" data-testid="settings-presets-card">
        <div className="p-4 border-b border-border flex items-center gap-3">
          <Bookmark className="h-5 w-5 text-[#E11D48]" />
          <div>
            <h2 className="font-heading text-xl font-bold tracking-tight">
              Пресеты полей ({presets.length})
            </h2>
            <p className="text-sm text-muted-foreground mt-0.5">
              Сохранённые наборы полей для быстрого заполнения. Создаются в редакторе договора.
            </p>
          </div>
        </div>
        {presets.length === 0 ? (
          <div className="px-4 py-8 text-center text-muted-foreground text-sm">
            Пресетов пока нет. Откройте редактор договора и нажмите «Сохранить пресет».
          </div>
        ) : (
          <div>
            {presets.map((p) => (
              <div
                key={p.id}
                className="flex items-center justify-between gap-3 px-4 py-3 border-b border-border"
                data-testid={`settings-preset-${p.id}`}
              >
                <div className="flex items-center gap-3">
                  <Bookmark className="h-4 w-4 text-[#E11D48]" />
                  <span className="text-sm font-medium">{p.name}</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="rounded-none text-[#FF3B30] hover:text-[#FF3B30] hover:bg-red-500/10"
                  onClick={() => handleDeletePreset(p.id)}
                  data-testid={`settings-preset-delete-${p.id}`}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Fields list */}
      <div className="bg-card border border-border">
        <div className="p-4 border-b border-border">
          <h2 className="font-heading text-xl font-bold tracking-tight">
            Поля автозаполнения ({FIELDS.length})
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Эти поля берутся из Excel и подставляются в договор.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {FIELDS.map((f, i) => (
            <div
              key={f.key}
              className="flex items-center gap-3 px-4 py-3 border-b border-r border-border"
              data-testid={`settings-field-${f.key}`}
            >
              <span className="font-heading text-sm font-bold text-[#E11D48] w-6">
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className="text-sm">{f.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
