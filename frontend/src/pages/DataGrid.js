import React, { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/Page";
import { toast } from "sonner";
import {
  Sheet as SheetIcon,
  Save,
  Plus,
  Loader2,
  Database,
  X,
  Search,
  Trash2,
} from "lucide-react";
import {
  getMasterSchema,
  getContractsGrid,
  saveMasterBulk,
  addCustomColumn,
  deleteCustomColumn,
  exportBase,
} from "@/lib/apiClient";

export default function DataGrid() {
  const [columns, setColumns] = useState([]);
  const [rows, setRows] = useState([]);
  const [dirty, setDirty] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [search, setSearch] = useState("");
  const [addOpen, setAddOpen] = useState(false);
  const [newColName, setNewColName] = useState("");
  const [newColSection, setNewColSection] = useState("Дополнительно");
  const [addingCol, setAddingCol] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const [schema, grid] = await Promise.all([getMasterSchema(), getContractsGrid()]);
      setColumns(schema.columns || []);
      setRows((grid.rows || []).map((r) => ({ ...r, master: { ...(r.master || {}) } })));
      setDirty(new Set());
    } catch (e) {
      toast.error("Не удалось загрузить таблицу");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  // Группировка колонок по секциям (для верхней строки-«шапки»)
  const sections = useMemo(() => {
    const out = [];
    for (const c of columns) {
      const last = out[out.length - 1];
      if (last && last.name === c.section) last.cols.push(c);
      else out.push({ name: c.section, cols: [c] });
    }
    return out;
  }, [columns]);

  const filteredRows = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) => {
      const fio = (r.master?.fio || r.full_name || "").toLowerCase();
      const num = (r.master?.contract_number || r.contract_number || "").toLowerCase();
      return fio.includes(q) || num.includes(q);
    });
  }, [rows, search]);

  function setCell(rowId, key, value) {
    setRows((prev) =>
      prev.map((r) =>
        r.id === rowId ? { ...r, master: { ...r.master, [key]: value } } : r
      )
    );
    setDirty((prev) => new Set(prev).add(rowId));
  }

  async function handleSave() {
    if (dirty.size === 0) {
      toast.info("Нет изменений для сохранения");
      return;
    }
    setSaving(true);
    try {
      const changed = rows
        .filter((r) => dirty.has(r.id))
        .map((r) => ({ id: r.id, master: r.master }));
      const res = await saveMasterBulk(changed);
      toast.success(`Сохранено строк: ${res.updated ?? changed.length}`);
      setDirty(new Set());
    } catch (e) {
      toast.error("Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  }

  async function handleAddColumn() {
    const name = newColName.trim();
    if (!name) {
      toast.error("Введите название столбца");
      return;
    }
    setAddingCol(true);
    try {
      await addCustomColumn(name, newColSection.trim() || "Дополнительно");
      toast.success(`Столбец «${name}» добавлен`);
      setNewColName("");
      setAddOpen(false);
      const schema = await getMasterSchema();
      setColumns(schema.columns || []);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Не удалось добавить столбец");
    } finally {
      setAddingCol(false);
    }
  }

  async function handleDeleteColumn(col) {
    if (col.builtin) return;
    if (!window.confirm(`Удалить столбец «${col.label}»? Данные в нём будут потеряны.`)) return;
    try {
      await deleteCustomColumn(col.key);
      toast.success("Столбец удалён");
      const schema = await getMasterSchema();
      setColumns(schema.columns || []);
    } catch (e) {
      toast.error("Не удалось удалить столбец");
    }
  }

  async function handleExportBase() {
    setExporting(true);
    try {
      await exportBase();
    } catch (e) {
      toast.error("Не удалось скачать базу");
    } finally {
      setExporting(false);
    }
  }

  const sectionColor = (name) => {
    // мягкие пастельные заголовки секций
    const map = {
      "Общие данные": "bg-rose-50 text-rose-700",
      "Паспорт": "bg-amber-50 text-amber-700",
      "Место рождения": "bg-emerald-50 text-emerald-700",
      "Место жительства (регистрация)": "bg-sky-50 text-sky-700",
      "Откуда прибыл": "bg-violet-50 text-violet-700",
      "Договор найма": "bg-pink-50 text-pink-700",
      "Регистрация / Сообщение": "bg-teal-50 text-teal-700",
      "Формы 19 / 24 — дополнительно": "bg-indigo-50 text-indigo-700",
      "Дополнительно": "bg-fuchsia-50 text-fuchsia-700",
    };
    return map[name] || "bg-slate-100 text-slate-700";
  };

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="База данных"
        title="Таблица данных (Excel)"
        subtitle="Редактируйте всю базу прямо здесь, как в Excel. Нажмите «Сохранить» — изменения сразу попадут во все документы."
        icon={SheetIcon}
        actions={
          <div className="flex items-center gap-2 flex-wrap">
            <Button
              variant="outline"
              className="h-11 border-pink-200"
              onClick={() => setAddOpen(true)}
              data-testid="datagrid-add-column-btn"
            >
              <Plus className="h-4 w-4" />
              Добавить столбец
            </Button>
            <Button
              variant="outline"
              className="h-11 border-pink-200"
              onClick={handleExportBase}
              disabled={exporting}
              data-testid="datagrid-export-btn"
            >
              {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Database className="h-4 w-4" />}
              Скачать Excel
            </Button>
            <Button
              className="h-11 bg-gradient-to-r from-rose-400 to-pink-500 hover:from-rose-500 hover:to-pink-600 text-white font-semibold"
              onClick={handleSave}
              disabled={saving || dirty.size === 0}
              data-testid="datagrid-save-btn"
            >
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Сохранить{dirty.size > 0 ? ` (${dirty.size})` : ""}
            </Button>
          </div>
        }
      />

      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[220px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Поиск по ФИО или номеру договора"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            data-testid="datagrid-search"
          />
        </div>
        <div className="text-sm text-muted-foreground">
          Строк: <b>{filteredRows.length}</b>
          {dirty.size > 0 && (
            <span className="ml-3 text-rose-600 font-medium">● несохранённые изменения</span>
          )}
        </div>
      </div>

      <div className="card-premium overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-24 text-muted-foreground">
            <Loader2 className="h-6 w-6 animate-spin mr-2" /> Загрузка базы…
          </div>
        ) : rows.length === 0 ? (
          <div className="py-24 text-center text-muted-foreground">
            В базе пока нет договоров. Создайте их через «Генерация из Excel».
          </div>
        ) : (
          <div className="overflow-auto max-h-[70vh] relative" data-testid="datagrid-table-wrap">
            <table className="border-collapse text-sm">
              <thead className="sticky top-0 z-20">
                {/* Строка секций */}
                <tr>
                  <th
                    className="sticky left-0 z-30 bg-white border border-slate-200 px-3 py-2 text-left min-w-[220px]"
                    rowSpan={2}
                  >
                    <span className="text-xs uppercase tracking-wide text-muted-foreground">
                      ФИО / № договора
                    </span>
                  </th>
                  {sections.map((s) => (
                    <th
                      key={s.name}
                      colSpan={s.cols.length}
                      className={`border border-slate-200 px-3 py-1.5 text-center text-xs font-semibold whitespace-nowrap ${sectionColor(
                        s.name
                      )}`}
                    >
                      {s.name}
                    </th>
                  ))}
                </tr>
                {/* Строка заголовков колонок */}
                <tr>
                  {columns.map((c) => (
                    <th
                      key={c.key}
                      className="bg-slate-50 border border-slate-200 px-2 py-2 text-left text-[11px] font-medium text-slate-600 align-bottom min-w-[150px] max-w-[220px]"
                    >
                      <div className="flex items-start justify-between gap-1">
                        <span className="leading-tight">{c.label}</span>
                        {!c.builtin && (
                          <button
                            onClick={() => handleDeleteColumn(c)}
                            className="text-slate-400 hover:text-rose-600 shrink-0"
                            title="Удалить столбец"
                            data-testid={`datagrid-del-col-${c.key}`}
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((r, ri) => (
                  <tr key={r.id} className="hover:bg-rose-50/40">
                    <td className="sticky left-0 z-10 bg-white border border-slate-200 px-3 py-1.5 min-w-[220px]">
                      <div className="font-medium text-slate-800 truncate max-w-[200px]">
                        {r.master?.fio || r.full_name || "—"}
                      </div>
                      <div className="text-[11px] text-muted-foreground truncate max-w-[200px]">
                        № {r.master?.contract_number || r.contract_number || "—"}
                        {r.status === "draft" && (
                          <span className="ml-1 text-amber-600">(черновик)</span>
                        )}
                      </div>
                    </td>
                    {columns.map((c) => {
                      const val = r.master?.[c.key] ?? "";
                      const cellId = `cell-${ri}-${c.key}`;
                      if (c.dropdown && c.dropdown.length) {
                        return (
                          <td key={c.key} className="border border-slate-200 p-0">
                            <select
                              className="w-full h-9 px-2 bg-transparent outline-none focus:bg-rose-50 focus:ring-1 focus:ring-rose-300 text-sm"
                              value={val}
                              onChange={(e) => setCell(r.id, c.key, e.target.value)}
                              data-testid={cellId}
                            >
                              <option value=""></option>
                              {c.dropdown.map((opt) => (
                                <option key={opt} value={opt}>
                                  {opt}
                                </option>
                              ))}
                            </select>
                          </td>
                        );
                      }
                      return (
                        <td key={c.key} className="border border-slate-200 p-0">
                          <input
                            className="w-full h-9 px-2 bg-transparent outline-none focus:bg-rose-50 focus:ring-1 focus:ring-rose-300 text-sm"
                            value={val}
                            onChange={(e) => setCell(r.id, c.key, e.target.value)}
                            data-testid={cellId}
                          />
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Диалог добавления столбца */}
      {addOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" data-testid="datagrid-add-dialog">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-800">Новый столбец</h3>
              <button onClick={() => setAddOpen(false)} className="text-slate-400 hover:text-slate-700">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-600">Название столбца</label>
              <Input
                autoFocus
                placeholder="Например: Срок обучения"
                value={newColName}
                onChange={(e) => setNewColName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAddColumn()}
                data-testid="datagrid-newcol-name"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-600">Секция (группа)</label>
              <Input
                placeholder="Дополнительно"
                value={newColSection}
                onChange={(e) => setNewColSection(e.target.value)}
                data-testid="datagrid-newcol-section"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setAddOpen(false)}>
                Отмена
              </Button>
              <Button
                className="bg-[#EC4899] hover:bg-[#DB2777] text-white"
                onClick={handleAddColumn}
                disabled={addingCol}
                data-testid="datagrid-newcol-confirm"
              >
                {addingCol ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
                Добавить
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
