import React, { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Link2, Plus, X, ChevronDown, ChevronRight, Loader2, ArrowLeft } from "lucide-react";
import {
  getMasterSchema,
  getDocumentTargets,
  getDependencies,
  addDependency,
  deleteDependency,
} from "@/lib/apiClient";

/**
 * Панель «Зависимости» для страницы документа.
 * Позволяет привязать любой столбец таблицы (в т.ч. свой) к полю бланка:
 * значение столбца автоматически подставится в этот документ при генерации.
 *
 * props: document -> "contract" | "forma19" | "forma24" | "soobshenie" | "zayavlenie"
 */
export default function DependencyManager({ document, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  const [loading, setLoading] = useState(false);
  const [columns, setColumns] = useState([]);
  const [targets, setTargets] = useState([]);
  const [docLabel, setDocLabel] = useState("");
  const [deps, setDeps] = useState([]);
  const [targetField, setTargetField] = useState("");
  const [source, setSource] = useState("");
  const [adding, setAdding] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [schema, tg, dp] = await Promise.all([
        getMasterSchema(),
        getDocumentTargets(document),
        getDependencies(document),
      ]);
      setColumns(schema.columns || []);
      setTargets(tg.targets || []);
      setDocLabel(tg.label || "");
      setDeps(dp.dependencies || []);
    } catch (e) {
      toast.error("Не удалось загрузить зависимости");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (open && columns.length === 0) load();
  }, [open]);

  async function handleAdd() {
    if (!targetField || !source) {
      toast.error("Выберите поле бланка и столбец");
      return;
    }
    setAdding(true);
    try {
      await addDependency(document, targetField, source);
      toast.success("Зависимость добавлена");
      setTargetField("");
      setSource("");
      const dp = await getDependencies(document);
      setDeps(dp.dependencies || []);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Не удалось добавить");
    } finally {
      setAdding(false);
    }
  }

  async function handleDelete(id) {
    try {
      await deleteDependency(id);
      setDeps((prev) => prev.filter((d) => d.id !== id));
      toast.success("Удалено");
    } catch (e) {
      toast.error("Не удалось удалить");
    }
  }

  const customCols = columns.filter((c) => !c.builtin);
  const builtinCols = columns.filter((c) => c.builtin);

  return (
    <div className="card-premium overflow-hidden" data-testid={`deps-panel-${document}`}>
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-rose-50/50 transition-colors"
        data-testid={`deps-toggle-${document}`}
      >
        <span className="flex items-center gap-2 font-semibold text-slate-800">
          <Link2 className="h-4 w-4 text-[#EC4899]" />
          Зависимости данных
          {deps.length > 0 && (
            <span className="ml-1 text-xs bg-[#EC4899] text-white rounded-full px-2 py-0.5">
              {deps.length}
            </span>
          )}
        </span>
        {open ? (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        )}
      </button>

      {open && (
        <div className="px-4 pb-4 pt-1 border-t border-border space-y-4">
          <p className="text-sm text-muted-foreground">
            Привяжите столбец таблицы к полю этого документа — его значение будет
            автоматически подставляться в бланк. Свои столбцы добавляются в разделе
            «Таблица данных».
          </p>

          {loading ? (
            <div className="flex items-center gap-2 text-muted-foreground py-4">
              <Loader2 className="h-4 w-4 animate-spin" /> Загрузка…
            </div>
          ) : (
            <>
              {/* Текущие зависимости */}
              {deps.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {deps.map((d) => (
                    <div
                      key={d.id}
                      className="flex items-center gap-2 bg-rose-50 border border-rose-200 rounded-lg px-3 py-1.5 text-sm"
                      data-testid={`dep-item-${d.id}`}
                    >
                      <span className="font-medium text-slate-700">{d.target_label}</span>
                      <ArrowLeft className="h-3.5 w-3.5 text-[#EC4899]" />
                      <span className="text-slate-600">{d.source_label}</span>
                      <button
                        onClick={() => handleDelete(d.id)}
                        className="text-slate-400 hover:text-rose-600 ml-1"
                        title="Удалить зависимость"
                        data-testid={`dep-del-${d.id}`}
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Добавление новой зависимости */}
              <div className="flex flex-wrap items-end gap-3 bg-slate-50 rounded-lg p-3">
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-slate-500">Поле бланка</label>
                  <select
                    className="h-10 min-w-[220px] px-2 rounded-md border border-slate-300 bg-white text-sm outline-none focus:ring-1 focus:ring-rose-300"
                    value={targetField}
                    onChange={(e) => setTargetField(e.target.value)}
                    data-testid={`dep-target-${document}`}
                  >
                    <option value="">— выберите поле —</option>
                    {targets.map((t) => (
                      <option key={t.field} value={t.field}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-xs text-slate-500">Столбец (источник)</label>
                  <select
                    className="h-10 min-w-[220px] px-2 rounded-md border border-slate-300 bg-white text-sm outline-none focus:ring-1 focus:ring-rose-300"
                    value={source}
                    onChange={(e) => setSource(e.target.value)}
                    data-testid={`dep-source-${document}`}
                  >
                    <option value="">— выберите столбец —</option>
                    {customCols.length > 0 && (
                      <optgroup label="Свои столбцы">
                        {customCols.map((c) => (
                          <option key={c.key} value={c.key}>
                            {c.label}
                          </option>
                        ))}
                      </optgroup>
                    )}
                    <optgroup label="Стандартные столбцы">
                      {builtinCols.map((c) => (
                        <option key={c.key} value={c.key}>
                          {c.label}
                        </option>
                      ))}
                    </optgroup>
                  </select>
                </div>

                <Button
                  className="h-10 bg-[#EC4899] hover:bg-[#DB2777] text-white"
                  onClick={handleAdd}
                  disabled={adding}
                  data-testid={`dep-add-${document}`}
                >
                  {adding ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                  Добавить зависимость
                </Button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
