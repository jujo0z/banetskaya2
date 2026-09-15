import React, { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import {
  Type, Minus, Database, Table2, Bold, Italic, Underline,
  AlignLeft, AlignCenter, AlignRight, Copy, Trash2, Save, RotateCcw, Plus,
} from "lucide-react";
import { getFormaTemplate, saveFormaTemplate, resetFormaTemplate } from "@/lib/apiClient";
import ZayavPreview from "@/components/ZayavPreview";

const uid = () => "u" + Math.random().toString(36).slice(2, 9);

export default function DocEditor({ which, values = {}, side = "front", setSide = () => {} }) {
  const page = side === "back" ? 2 : 1;
  const [template, setTemplate] = useState([]);
  const [slots, setSlots] = useState([]);
  const [pageWmm, setPageWmm] = useState(105);
  const [pageHmm, setPageHmm] = useState(145);
  const [selectedId, setSelectedId] = useState(null);
  const [editingId, setEditingId] = useState(null);
  const [selectedCell, setSelectedCell] = useState(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const data = await getFormaTemplate(which);
        setTemplate((data.template || []).map((e) => ({ ...e, id: e.id || uid() })));
        setSlots(data.slots || []);
        if (data.page_w_mm) setPageWmm(data.page_w_mm);
        if (data.page_h_mm) setPageHmm(data.page_h_mm);
      } catch (e) {
        toast.error("Не удалось загрузить шаблон");
      } finally {
        setLoading(false);
      }
    })();
  }, [which]);

  const pageElements = useMemo(() => template.filter((e) => Number(e.page || 1) === page), [template, page]);
  const selectedEl = useMemo(() => template.find((e) => e.id === selectedId) || null, [template, selectedId]);
  const isText = selectedEl && (selectedEl.type === "text" || selectedEl.type === "field");
  const isLine = selectedEl && selectedEl.type === "line";
  const isRect = selectedEl && selectedEl.type === "rect";
  const isGrid = selectedEl && selectedEl.type === "grid";

  const updateEl = (id, patch) => setTemplate((t) => t.map((e) => (e.id === id ? { ...e, ...patch } : e)));
  const deleteEl = (id) => { setTemplate((t) => t.filter((e) => e.id !== id)); setSelectedId(null); setSelectedCell(null); };
  const dupEl = (id) => setTemplate((t) => {
    const el = t.find((e) => e.id === id); if (!el) return t;
    const copy = { ...el, id: uid(), x: Math.min(96, (el.x || 0) + 2), y: Math.min(97, (el.y || 0) + 2) };
    setSelectedId(copy.id); return [...t, copy];
  });
  const addText = () => setTemplate((t) => {
    const el = { id: uid(), type: "text", page, x: 20, y: 20, align: "left", text: "Новый текст", size: 6.5, bold: false, italic: false, font: "sans", color: "#17171f" };
    setSelectedId(el.id); return [...t, el];
  });
  const addLine = () => setTemplate((t) => {
    const el = { id: uid(), type: "line", page, x: 10, y: 30, w: 40, thickness: 0.5, color: "#17171f" };
    setSelectedId(el.id); return [...t, el];
  });
  const addField = () => setTemplate((t) => {
    const first = (slots[0] && slots[0].slot) || "surname";
    const el = { id: uid(), type: "field", field: first, page, x: 30, y: 30, align: "left", size: 7, bold: true, italic: false, font: "sans", color: "#0a0d52", w: 0 };
    setSelectedId(el.id); return [...t, el];
  });
  const addGrid = () => setTemplate((t) => {
    const el = {
      id: uid(), type: "grid", page, x: 20, y: 20,
      cols: [5, 5, 5, 5, 5], rows: [5], cells: {},
      thickness: 0.4, color: "#17171f", size: 8, font: "sans",
    };
    setSelectedId(el.id); setSelectedCell(null); return [...t, el];
  });
  const commitText = (id, text) => { updateEl(id, { text }); setEditingId(null); };

  // ---- grid helpers ----
  const gridAddCol = () => updateEl(selectedEl.id, { cols: [...(selectedEl.cols || []), 5] });
  const gridDelCol = () => selectedEl.cols?.length > 1 && updateEl(selectedEl.id, { cols: selectedEl.cols.slice(0, -1) });
  const gridAddRow = () => updateEl(selectedEl.id, { rows: [...(selectedEl.rows || []), 5] });
  const gridDelRow = () => selectedEl.rows?.length > 1 && updateEl(selectedEl.id, { rows: selectedEl.rows.slice(0, -1) });
  const setCell = (patch) => {
    if (!selectedCell) return;
    const g = template.find((e) => e.id === selectedCell.gridId);
    if (!g) return;
    const key = `${selectedCell.r}_${selectedCell.c}`;
    const cells = { ...(g.cells || {}) };
    cells[key] = { ...(cells[key] || {}), ...patch };
    updateEl(g.id, { cells });
  };
  const curCell = () => {
    if (!selectedCell) return {};
    const g = template.find((e) => e.id === selectedCell.gridId);
    return (g && g.cells && g.cells[`${selectedCell.r}_${selectedCell.c}`]) || {};
  };
  const onCellClick = (gridId, r, c) => setSelectedCell({ gridId, r, c });

  const doSave = async () => {
    setSaving(true);
    try { await saveFormaTemplate(which, template.map(({ ...e }) => e)); toast.success("Шаблон сохранён — применён везде (печать и пакет)"); }
    catch { toast.error("Не удалось сохранить шаблон"); }
    finally { setSaving(false); }
  };
  const doReset = async () => {
    if (!window.confirm("Сбросить бланк к оригиналу? Все правки шаблона будут удалены.")) return;
    setSaving(true);
    try {
      const res = await resetFormaTemplate(which);
      setTemplate((res.template || []).map((e) => ({ ...e, id: e.id || uid() })));
      setSelectedId(null); setEditingId(null); setSelectedCell(null);
      toast.success("Шаблон сброшен к оригиналу");
    } catch { toast.error("Не удалось сбросить"); }
    finally { setSaving(false); }
  };

  if (loading) return <div className="p-6 text-muted-foreground">Загрузка редактора…</div>;

  const cell = curCell();

  return (
    <div className="space-y-2">
      {/* лента-тулбар */}
      <div className="rounded-md border border-amber-400/40 bg-[#FDECF5] px-2 py-1.5 flex flex-wrap items-center gap-1.5 sticky top-0 z-20" data-testid="doc-ribbon">
        <div className="flex rounded-md border border-pink-100 overflow-hidden mr-1">
          <button type="button" onClick={() => setSide("front")} className={`px-2.5 py-1 text-xs ${side === "front" ? "bg-[#EC4899] text-white font-semibold" : "hover:bg-white"}`} data-testid="doc-side-front">Лицо</button>
          <button type="button" onClick={() => setSide("back")} className={`px-2.5 py-1 text-xs ${side === "back" ? "bg-[#EC4899] text-white font-semibold" : "hover:bg-white"}`} data-testid="doc-side-back">Оборот</button>
        </div>
        <button onClick={addText} title="Добавить текст" className="flex items-center gap-1 h-7 px-2 rounded border border-pink-100 text-xs hover:bg-white" data-testid="doc-add-text"><Type className="h-3.5 w-3.5" /> Текст</button>
        <button onClick={addLine} title="Добавить линию" className="flex items-center gap-1 h-7 px-2 rounded border border-pink-100 text-xs hover:bg-white" data-testid="doc-add-line"><Minus className="h-3.5 w-3.5" /> Линия</button>
        <button onClick={addField} title="Ячейка, которую программа заполнит из данных" className="flex items-center gap-1 h-7 px-2 rounded border border-[#2563eb]/50 bg-[#2563eb]/15 text-[#1d4ed8] text-xs hover:bg-[#2563eb]/25" data-testid="doc-add-field"><Database className="h-3.5 w-3.5" /> Поле</button>
        <button onClick={addGrid} title="Добавить таблицу-клеточки (как в Excel)" className="flex items-center gap-1 h-7 px-2 rounded border border-emerald-500/50 bg-emerald-500/15 text-emerald-700 text-xs hover:bg-emerald-500/25" data-testid="doc-add-grid"><Table2 className="h-3.5 w-3.5" /> Таблица</button>
        <span className="w-px h-6 bg-black/10 mx-1" />

        {!selectedEl && <span className="text-[11px] text-muted-foreground">Выберите элемент в бланке…</span>}

        {isText && (
          <>
            <select value={selectedEl.font || "sans"} onChange={(e) => updateEl(selectedEl.id, { font: e.target.value })} className="h-7 rounded bg-white/70 border border-pink-100 text-xs px-1" data-testid="doc-font" title="Шрифт">
              <option value="sans">Arial</option>
              <option value="serif">Times New Roman</option>
            </select>
            <div className="flex items-center h-7 rounded border border-pink-100 overflow-hidden">
              <button onClick={() => updateEl(selectedEl.id, { size: Math.max(3, +((selectedEl.size || 7) - 0.5).toFixed(1)) })} className="px-1.5 hover:bg-white text-sm">−</button>
              <input type="number" step="0.1" value={selectedEl.size ?? ""} onChange={(e) => updateEl(selectedEl.id, { size: parseFloat(e.target.value) })} className="w-12 h-full bg-white/70 text-center text-xs outline-none" data-testid="doc-size" />
              <button onClick={() => updateEl(selectedEl.id, { size: +((selectedEl.size || 7) + 0.5).toFixed(1) })} className="px-1.5 hover:bg-white text-sm">+</button>
            </div>
            <button onClick={() => updateEl(selectedEl.id, { bold: !selectedEl.bold })} className={`h-7 w-7 grid place-items-center rounded border border-pink-100 ${selectedEl.bold ? "bg-white/60" : "hover:bg-white"}`} data-testid="doc-bold"><Bold className="h-3.5 w-3.5" /></button>
            <button onClick={() => updateEl(selectedEl.id, { italic: !selectedEl.italic })} className={`h-7 w-7 grid place-items-center rounded border border-pink-100 ${selectedEl.italic ? "bg-white/60" : "hover:bg-white"}`} data-testid="doc-italic"><Italic className="h-3.5 w-3.5" /></button>
            <button onClick={() => updateEl(selectedEl.id, { underline: !selectedEl.underline })} className={`h-7 w-7 grid place-items-center rounded border border-pink-100 ${selectedEl.underline ? "bg-white/60" : "hover:bg-white"}`}><Underline className="h-3.5 w-3.5" /></button>
            {[["left", AlignLeft], ["center", AlignCenter], ["right", AlignRight]].map(([a, Ic]) => (
              <button key={a} onClick={() => updateEl(selectedEl.id, { align: a })} className={`h-7 w-7 grid place-items-center rounded border border-pink-100 ${selectedEl.align === a ? "bg-white/60" : "hover:bg-white"}`}><Ic className="h-3.5 w-3.5" /></button>
            ))}
            <input type="color" value={selectedEl.color || "#17171f"} onChange={(e) => updateEl(selectedEl.id, { color: e.target.value })} className="h-7 w-8 rounded border border-pink-100 bg-transparent p-0.5" title="Цвет" />
            {selectedEl.type === "field" && (
              <select value={selectedEl.field} onChange={(e) => updateEl(selectedEl.id, { field: e.target.value })} className="h-7 rounded bg-white/70 border border-pink-100 text-xs px-1 max-w-[180px]" data-testid="doc-field-select" title="Поле данных">
                {slots.map((s) => (<option key={s.slot} value={s.slot}>{s.label}</option>))}
              </select>
            )}
          </>
        )}

        {isLine && (
          <>
            <span className="text-[11px] text-muted-foreground">Линия:</span>
            <label className="text-[11px] text-muted-foreground">длина</label>
            <input type="number" step="0.5" value={selectedEl.w ?? ""} onChange={(e) => updateEl(selectedEl.id, { w: parseFloat(e.target.value), x2: undefined, y2: undefined })} className="w-16 h-7 bg-white/70 border border-pink-100 rounded text-center text-xs" />
            <label className="text-[11px] text-muted-foreground">толщина</label>
            <input type="number" step="0.1" value={selectedEl.thickness ?? ""} onChange={(e) => updateEl(selectedEl.id, { thickness: parseFloat(e.target.value) })} className="w-14 h-7 bg-white/70 border border-pink-100 rounded text-center text-xs" />
            <input type="color" value={selectedEl.color || "#17171f"} onChange={(e) => updateEl(selectedEl.id, { color: e.target.value })} className="h-7 w-8 rounded border border-pink-100 bg-transparent p-0.5" title="Цвет" />
          </>
        )}

        {isRect && (
          <>
            <span className="text-[11px] text-muted-foreground">Заливка:</span>
            <input type="color" value={selectedEl.fill || "#e6e6e8"} onChange={(e) => updateEl(selectedEl.id, { fill: e.target.value })} className="h-7 w-8 rounded border border-pink-100 bg-transparent p-0.5" title="Цвет заливки" />
            <label className="text-[11px] text-muted-foreground">Ш%</label>
            <input type="number" step="0.5" value={selectedEl.w ?? ""} onChange={(e) => updateEl(selectedEl.id, { w: parseFloat(e.target.value) })} className="w-14 h-7 bg-white/70 border border-pink-100 rounded text-center text-xs" />
            <label className="text-[11px] text-muted-foreground">В%</label>
            <input type="number" step="0.5" value={selectedEl.h ?? ""} onChange={(e) => updateEl(selectedEl.id, { h: parseFloat(e.target.value) })} className="w-14 h-7 bg-white/70 border border-pink-100 rounded text-center text-xs" />
          </>
        )}

        {isGrid && (
          <>
            <span className="text-[11px] text-muted-foreground">Таблица:</span>
            <button onClick={gridAddCol} className="h-7 px-2 rounded border border-pink-100 text-xs hover:bg-white" title="Добавить столбец">+ столбец</button>
            <button onClick={gridDelCol} className="h-7 px-2 rounded border border-pink-100 text-xs hover:bg-white" title="Убрать столбец">− столбец</button>
            <button onClick={gridAddRow} className="h-7 px-2 rounded border border-pink-100 text-xs hover:bg-white" title="Добавить строку">+ строка</button>
            <button onClick={gridDelRow} className="h-7 px-2 rounded border border-pink-100 text-xs hover:bg-white" title="Убрать строку">− строка</button>
            <label className="text-[11px] text-muted-foreground">ширина клетки %</label>
            <input type="number" step="0.5" value={(selectedEl.cols && selectedEl.cols[0]) || 5} onChange={(e) => updateEl(selectedEl.id, { cols: (selectedEl.cols || []).map(() => parseFloat(e.target.value) || 5) })} className="w-14 h-7 bg-white/70 border border-pink-100 rounded text-center text-xs" />
            <label className="text-[11px] text-muted-foreground">высота %</label>
            <input type="number" step="0.5" value={(selectedEl.rows && selectedEl.rows[0]) || 5} onChange={(e) => updateEl(selectedEl.id, { rows: (selectedEl.rows || []).map(() => parseFloat(e.target.value) || 5) })} className="w-14 h-7 bg-white/70 border border-pink-100 rounded text-center text-xs" />
          </>
        )}

        <span className="flex-1" />
        {selectedEl && (
          <>
            <button onClick={() => dupEl(selectedEl.id)} title="Дублировать" className="h-7 w-7 grid place-items-center rounded border border-pink-100 hover:bg-white"><Copy className="h-3.5 w-3.5" /></button>
            <button onClick={() => deleteEl(selectedEl.id)} title="Удалить" className="h-7 w-7 grid place-items-center rounded border border-pink-100 hover:bg-[#EC4899]/30" data-testid="doc-delete"><Trash2 className="h-3.5 w-3.5" /></button>
            <span className="w-px h-6 bg-black/10 mx-1" />
          </>
        )}
        <button onClick={doSave} disabled={saving} className="flex items-center gap-1 h-7 px-2 rounded bg-amber-500 hover:bg-amber-600 text-black text-xs font-semibold" data-testid="doc-save"><Save className="h-3.5 w-3.5" /> Сохранить</button>
        <button onClick={doReset} disabled={saving} className="flex items-center gap-1 h-7 px-2 rounded border border-pink-100 text-xs hover:bg-white" data-testid="doc-reset"><RotateCcw className="h-3.5 w-3.5" /> Сбросить</button>
      </div>

      {/* панель редактирования клетки таблицы */}
      {isGrid && selectedCell && selectedCell.gridId === selectedEl.id && (
        <div className="rounded-md border border-emerald-400/50 bg-emerald-50 px-2 py-1.5 flex flex-wrap items-center gap-1.5" data-testid="doc-cell-panel">
          <span className="text-[11px] font-semibold text-emerald-700">Клетка [{selectedCell.r + 1};{selectedCell.c + 1}]:</span>
          <input value={cell.text || ""} onChange={(e) => setCell({ text: e.target.value, field: undefined })} placeholder="текст" className="h-7 w-32 bg-white border border-emerald-200 rounded text-xs px-2" data-testid="doc-cell-text" />
          <span className="text-[11px] text-muted-foreground">или поле:</span>
          <select value={cell.field || ""} onChange={(e) => setCell({ field: e.target.value || undefined, text: e.target.value ? undefined : cell.text })} className="h-7 rounded bg-white border border-emerald-200 text-xs px-1 max-w-[180px]" data-testid="doc-cell-field">
            <option value="">— нет —</option>
            {slots.map((s) => (<option key={s.slot} value={s.slot}>{s.label}</option>))}
          </select>
          <button onClick={() => setCell({ bold: !cell.bold })} className={`h-7 w-7 grid place-items-center rounded border border-emerald-200 ${cell.bold ? "bg-emerald-200" : "bg-white"}`}><Bold className="h-3.5 w-3.5" /></button>
          <label className="text-[11px] text-muted-foreground">кегль</label>
          <input type="number" step="0.5" value={cell.size || selectedEl.size || 8} onChange={(e) => setCell({ size: parseFloat(e.target.value) })} className="w-14 h-7 bg-white border border-emerald-200 rounded text-center text-xs" />
          <button onClick={() => setSelectedCell(null)} className="h-7 px-2 rounded border border-emerald-200 text-xs bg-white hover:bg-emerald-100">Готово</button>
        </div>
      )}

      <p className="text-[11px] text-muted-foreground px-1">
        Клик — выбрать; тащить за красный маркер — двигать; 2× клик по тексту — изменить надпись.
        {isGrid ? " Кликните по клетке таблицы, чтобы вписать текст или назначить поле данных." : " Кнопка «Таблица» добавляет клеточки, как в Excel."}
        {" "}Изменения применяются к печати формы и к «Полному пакету» после нажатия «Сохранить».
      </p>

      <div className="rounded-lg border border-pink-100 bg-white/80 p-3 shadow-2xl overflow-auto" style={{ maxHeight: "80vh" }}>
        <div className="mx-auto ring-1 ring-black/10" style={{ maxWidth: 620 }}>
          <ZayavPreview
            page={page}
            elements={pageElements}
            values={values}
            editMode
            pageWmm={pageWmm}
            pageHmm={pageHmm}
            selectedId={selectedId}
            editingId={editingId}
            selectedCell={selectedCell}
            onSelect={(id) => { setSelectedId(id); if (id === null) setSelectedCell(null); }}
            onStartTextEdit={setEditingId}
            onCommitText={commitText}
            onChange={updateEl}
            onCellClick={onCellClick}
          />
        </div>
      </div>
    </div>
  );
}
