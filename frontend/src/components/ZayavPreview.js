import React, { useRef, useState, useEffect, useCallback } from "react";

const A4_W_PT = 595.2756;
const SERIF = '"Times New Roman", "Liberation Serif", "PT Serif", serif';
const SANS = '"Arial", "Liberation Sans", system-ui, sans-serif';

function measureWidth(text, fontPx, bold, fam) {
  if (!measureWidth._c) measureWidth._c = document.createElement("canvas").getContext("2d");
  const c = measureWidth._c;
  c.font = `${bold ? "700" : "400"} ${fontPx}px ${fam}`;
  return c.measureText(text || "").width;
}

/**
 * Страница «Заявления» = список редактируемых элементов шаблона.
 * type: 'text' | 'field' | 'line'.  mode: 'view' | 'edit'.
 */
export default function ZayavPreview({
  page,
  elements,       // элементы ТОЛЬКО этой страницы
  values,         // {field: text} — значения данных
  editMode = false,
  selectedId = null,
  editingId = null,
  onSelect = () => {},
  onStartTextEdit = () => {},
  onCommitText = () => {},
  onChange = () => {},
}) {
  const ref = useRef(null);
  const [W, setW] = useState(800);
  const dragRef = useRef(null);
  const editRef = useRef(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const update = () => setW(el.clientWidth || 800);
    update();
    let ro;
    if (typeof ResizeObserver !== "undefined") {
      ro = new ResizeObserver(update);
      ro.observe(el);
    }
    window.addEventListener("resize", update);
    return () => { if (ro) ro.disconnect(); window.removeEventListener("resize", update); };
  }, []);

  useEffect(() => {
    if (editingId && editRef.current) {
      const node = editRef.current;
      node.focus();
      // курсор в конец
      const r = document.createRange();
      r.selectNodeContents(node);
      r.collapse(false);
      const sel = window.getSelection();
      sel.removeAllRanges();
      sel.addRange(r);
    }
  }, [editingId]);

  const onPointerMove = useCallback((e) => {
    const d = dragRef.current;
    if (!d) return;
    const dx = ((e.clientX - d.startX) / d.rw) * 100;
    const dy = ((e.clientY - d.startY) / d.rh) * 100;
    if (!d.moved && Math.abs(e.clientX - d.startX) + Math.abs(e.clientY - d.startY) < 3) return;
    d.moved = true;
    onChange(d.id, {
      x: Math.max(0, Math.min(100, +(d.ox + dx).toFixed(2))),
      y: Math.max(0, Math.min(100, +(d.oy + dy).toFixed(2))),
    });
  }, [onChange]);

  const onPointerUp = useCallback(() => {
    dragRef.current = null;
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", onPointerUp);
  }, [onPointerMove]);

  const startDrag = (e, el) => {
    if (!editMode || editingId === el.id) return;
    e.preventDefault();
    e.stopPropagation();
    onSelect(el.id);
    const rect = ref.current.getBoundingClientRect();
    dragRef.current = { id: el.id, startX: e.clientX, startY: e.clientY, ox: el.x, oy: el.y, rw: rect.width, rh: rect.height, moved: false };
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
  };

  const pxPerPt = W / A4_W_PT;

  const renderTextLike = (el) => {
    const fam = el.font === "sans" ? SANS : SERIF;
    const isField = el.type === "field";
    const val = isField ? (values ? values[el.field] : "") : el.text;
    const hasVal = val != null && String(val).trim() !== "";
    const shown = hasVal ? String(val) : (isField ? (editMode ? `《${el.field}》` : "") : (el.text || ""));
    if (!editMode && shown === "") return null;

    let fontPx = (el.size || 9) * pxPerPt;
    if (el.w && el.w > 0) {
      const boxW = (el.w / 100) * W;
      const tw = measureWidth(shown || " ", fontPx, el.bold, fam);
      if (tw > boxW) fontPx = Math.max(4 * pxPerPt, fontPx * (boxW / tw));
    }
    const align = el.align || "left";
    const tx = align === "center" ? "-50%" : align === "right" ? "-100%" : "0";
    const isSel = editMode && selectedId === el.id;
    const editing = editingId === el.id;

    const common = {
      position: "absolute",
      left: `${el.x}%`,
      top: `${el.y}%`,
      transform: `translate(${tx}, -0.82em)`,
      transformOrigin: "left top",
      fontFamily: fam,
      fontSize: `${fontPx}px`,
      lineHeight: 1,
      fontWeight: el.bold ? 700 : 400,
      fontStyle: el.italic ? "italic" : "normal",
      color: el.color || (isField ? "#0a0d52" : "#17171f"),
      whiteSpace: "nowrap",
    };

    if (editing && !isField) {
      return (
        <div
          key={el.id}
          ref={editRef}
          contentEditable
          suppressContentEditableWarning
          onBlur={(e) => onCommitText(el.id, e.currentTarget.textContent)}
          onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); e.currentTarget.blur(); } }}
          data-testid={`zayav-el-${el.id}`}
          style={{ ...common, outline: "1px solid #2563eb", background: "rgba(37,99,235,.12)", cursor: "text", minWidth: 6 }}
        >
          {el.text}
        </div>
      );
    }

    return (
      <div
        key={el.id}
        onPointerDown={(e) => startDrag(e, el)}
        onDoubleClick={() => { if (editMode && !isField) onStartTextEdit(el.id); }}
        title={isField ? `Поле: ${el.field}` : (editMode ? "2× клик — редактировать текст" : "")}
        data-testid={`zayav-el-${el.id}`}
        style={{
          ...common,
          cursor: editMode ? "move" : "default",
          outline: isSel ? "1px dashed #E11D48" : (editMode ? "1px dotted rgba(120,120,140,.35)" : "none"),
          background: isSel ? "rgba(225,29,72,.08)" : (editMode && isField ? "rgba(37,99,235,.05)" : "transparent"),
        }}
      >
        {shown === "" ? "\u00A0" : shown}
      </div>
    );
  };

  const renderLine = (el) => {
    const isSel = editMode && selectedId === el.id;
    const thick = Math.max(1, (el.thickness || 0.5) * pxPerPt);
    return (
      <div
        key={el.id}
        onPointerDown={(e) => startDrag(e, el)}
        data-testid={`zayav-el-${el.id}`}
        title={editMode ? "Линия" : ""}
        style={{
          position: "absolute",
          left: `${el.x}%`,
          top: `${el.y}%`,
          width: `${el.w}%`,
          height: `${thick}px`,
          background: el.color || "#17171f",
          cursor: editMode ? "move" : "default",
          outline: isSel ? "1px dashed #E11D48" : "none",
          outlineOffset: "2px",
        }}
      />
    );
  };

  return (
    <div
      ref={ref}
      onPointerDown={(e) => { if (editMode && e.target === ref.current) onSelect(null); }}
      style={{ position: "relative", width: "100%", aspectRatio: "210 / 297", background: "#fff" }}
      data-testid={`zayav-page-${page}`}
    >
      {(elements || []).map((el) => (el.type === "line" ? renderLine(el) : renderTextLike(el)))}
    </div>
  );
}
