import React, { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Activity, CheckCircle2, XCircle, Info, RefreshCw, ShieldCheck, ShieldAlert, Download } from "lucide-react";
import { getDiagnostics } from "@/lib/apiClient";
import { IS_DESKTOP } from "@/lib/env";

export default function Diagnostics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const run = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getDiagnostics();
      setData(res);
    } catch (e) {
      toast.error("Не удалось выполнить проверку");
      setData({ checks: [], all_ok: false });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    run();
  }, [run]);

  const checks = data?.checks || [];
  const allOk = data?.all_ok;

  const saveReport = () => {
    if (!data) return;
    const now = new Date();
    const lines = [];
    lines.push("Banetskaya.by — отчёт проверки системы");
    lines.push("Дата: " + now.toLocaleString("ru-RU"));
    lines.push("Платформа: " + (data.platform || "?") + (data.is_desktop ? " (приложение)" : " (веб)"));
    lines.push("Итог: " + (allOk ? "ВСЁ ГОТОВО К РАБОТЕ" : "ЕСТЬ ЗАМЕЧАНИЯ"));
    lines.push("".padEnd(48, "-"));
    checks.forEach((c) => {
      const mark = c.ok ? (c.info ? "[i]" : "[OK]") : "[!!]";
      lines.push(`${mark} ${c.label}: ${c.detail || ""}`);
    });
    const blob = new Blob([lines.join("\r\n")], { type: "text/plain;charset=utf-8" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `diagnostics_${now.toISOString().slice(0, 19).replace(/[:T]/g, "-")}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    toast.success("Отчёт сохранён — пришлите файл при обращении в поддержку");
  };

  return (
    <div className="p-6 lg:p-8 space-y-6" data-testid="diagnostics-page">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl font-bold tracking-tight flex items-center gap-3">
            <Activity className="h-8 w-8 text-[#E11D48]" /> Проверка системы
          </h1>
          <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
            Приложение само проверяет, всё ли на месте для работы: база данных, шрифты (кириллица),
            бланк, LibreOffice (экспорт в PDF), генерация PDF и принтеры. Запускайте после установки
            или при любых сбоях — так сразу видно, что не так.
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={saveReport} disabled={!data} variant="outline" data-testid="btn-save-report">
            <Download className="h-4 w-4 mr-2" /> Сохранить отчёт
          </Button>
          <Button onClick={run} disabled={loading} className="bg-[#E11D48] hover:bg-[#BE123C]" data-testid="btn-recheck">
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} /> Проверить снова
          </Button>
        </div>
      </div>

      {/* Overall banner */}
      {data && (
        <div
          className={`rounded-xl border p-4 flex items-center gap-3 ${
            allOk ? "border-emerald-500/40 bg-emerald-500/10" : "border-amber-500/40 bg-amber-500/10"
          }`}
          data-testid="diag-banner"
        >
          {allOk ? (
            <ShieldCheck className="h-7 w-7 text-emerald-400 shrink-0" />
          ) : (
            <ShieldAlert className="h-7 w-7 text-amber-400 shrink-0" />
          )}
          <div>
            <div className="font-semibold">
              {allOk ? "Всё готово к работе" : "Есть замечания — смотрите ниже"}
            </div>
            <div className="text-sm text-muted-foreground">
              {IS_DESKTOP ? "Проверка выполнена на этом компьютере." : "Веб-версия: часть проверок (принтеры) доступна только в Windows-приложении."}
            </div>
          </div>
        </div>
      )}

      {/* Checks */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {checks.map((c) => {
          const info = c.info && c.ok;
          return (
            <div
              key={c.key}
              className={`rounded-lg border p-4 flex items-start gap-3 ${
                c.ok ? (info ? "border-sky-500/30 bg-sky-500/5" : "border-emerald-500/25 bg-emerald-500/5") : "border-[#E11D48]/40 bg-[#E11D48]/10"
              }`}
              data-testid={`diag-${c.key}`}
            >
              {c.ok ? (
                info ? <Info className="h-5 w-5 text-sky-400 shrink-0 mt-0.5" /> : <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
              ) : (
                <XCircle className="h-5 w-5 text-[#E11D48] shrink-0 mt-0.5" />
              )}
              <div className="min-w-0">
                <div className="font-medium">{c.label}</div>
                <div className="text-xs text-muted-foreground break-words">{c.detail}</div>
              </div>
            </div>
          );
        })}
      </div>

      {loading && checks.length === 0 && (
        <div className="text-muted-foreground">Выполняется проверка…</div>
      )}
    </div>
  );
}
