import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Download, FileCheck2, Info } from "lucide-react";
import { toast } from "sonner";
import { FIELDS } from "@/lib/fields";
import { downloadSampleTemplate } from "@/lib/apiClient";

export default function Settings() {
  const [downloading, setDownloading] = useState(false);

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
      <div className="bg-white border border-border p-6">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 bg-[#F0F4FF] flex items-center justify-center shrink-0">
            <FileCheck2 className="h-5 w-5 text-[#002FA7]" strokeWidth={2} />
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
      <div className="bg-white border border-border p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="font-heading text-xl font-bold tracking-tight">Образец Excel</h2>
            <p className="text-sm text-muted-foreground mt-1 max-w-xl">
              Скачайте готовый файл с нужными колонками и примером строки — заполните своими данными и
              загрузите на вкладке «Генерация».
            </p>
          </div>
          <Button
            className="rounded-none bg-[#002FA7] hover:bg-[#00207A] text-white h-11"
            onClick={handleSample}
            disabled={downloading}
            data-testid="settings-download-sample-btn"
          >
            <Download className="h-4 w-4" />
            Скачать шаблон Excel
          </Button>
        </div>
      </div>

      {/* Fields list */}
      <div className="bg-white border border-border">
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
              <span className="font-heading text-sm font-bold text-[#002FA7] w-6">
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
