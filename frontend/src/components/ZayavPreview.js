import React, { useRef, useState, useEffect, useCallback } from "react";

// Размеры A4 в пунктах (совпадают с backend reportlab)
const A4_W_PT = 595.2756;
const SERIF = '"Times New Roman", "Liberation Serif", "PT Serif", serif';

// Измерение ширины строки в px тем же шрифтом (для авто-уменьшения)
function measureWidth(text, fontPx, bold) {
  if (!measureWidth._c) {
    measureWidth._c = document.createElement("canvas").getContext("2d");
  }
  const c = measureWidth._c;
  c.font = `${bold ? "700" : "400"} ${fontPx}px ${SERIF}`;
  return c.measureText(text || "").width;
}

/**
 * Предпросмотр одной страницы «Заявления»:
 * фон = чистый бланк (изображение) + слой данных по координатам (% страницы).
 * Та же система координат используется в PDF на бэкенде.
 */
export default function ZayavPreview({
  page,
  backgroundUrl,
  slots,          // { slotKey: {x,y,w,align,size,bold,label} }  (только для этой страницы)
  values,         // { slotKey: text }
  editMode = false,
  selectedSlot = null,
  onSelectSlot = () => {},
  onChangeSlot = () => {},
}) {
  const ref = useRef(null);
  const [W, setW] = useState(800);
  const dragRef = useRef(null);

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
    return () => {
      if (ro) ro.disconnect();
      window.removeEventListener("resize", update);
    };
  }, []);

  const onPointerMove = useCallback(
    (e) => {
      const d = dragRef.current;
      if (!d) return;
      const dx = ((e.clientX - d.startX) / d.rw) * 100;
      const dy = ((e.clientY - d.startY) / d.rh) * 100;
      onChangeSlot(d.slot, {
        x: Math.max(0, Math.min(100, +(d.ox + dx).toFixed(2))),
        y: Math.max(0, Math.min(100, +(d.oy + dy).toFixed(2))),
      });
    },
    [onChangeSlot]
  );

  const onPointerUp = useCallback(() => {
    dragRef.current = null;
    window.removeEventListener("pointermove", onPointerMove);
    window.removeEventListener("pointerup", onPointerUp);
  }, [onPointerMove]);

  const onPointerDown = (e, slot, cfg) => {
    if (!editMode) return;
    e.preventDefault();
    e.stopPropagation();
    onSelectSlot(slot);
    const rect = ref.current.getBoundingClientRect();
    dragRef.current = {
      slot,
      startX: e.clientX,
      startY: e.clientY,
      ox: cfg.x,
      oy: cfg.y,
      rw: rect.width,
      rh: rect.height,
    };
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerup", onPointerUp);
  };

  return (
    <div
      ref={ref}
      style={{ position: "relative", width: "100%", aspectRatio: "210 / 297", background: "#fff" }}
      data-testid={`zayav-page-${page}`}
    >
      <img
        src={backgroundUrl}
        alt=""
        draggable={false}
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", userSelect: "none", pointerEvents: "none" }}
      />
      {Object.entries(slots || {}).map(([slot, cfg]) => {
        const raw = values ? values[slot] : "";
        const hasVal = raw != null && String(raw).trim() !== "";
        const text = hasVal ? String(raw) : editMode ? cfg.label || slot : "";
        if (text === "") return null;
        let fontPx = (cfg.size || 9) * (W / A4_W_PT);
        const boxW = ((cfg.w || 20) / 100) * W;
        const tw = measureWidth(text, fontPx, cfg.bold);
        if (boxW > 0 && tw > boxW) {
          fontPx = Math.max(4 * (W / A4_W_PT), fontPx * (boxW / tw));
        }
        const isSel = editMode && selectedSlot === slot;
        return (
          <div
            key={slot}
            onPointerDown={(e) => onPointerDown(e, slot, cfg)}
            title={cfg.label || slot}
            data-testid={`zayav-slot-${slot}`}
            style={{
              position: "absolute",
              left: `${cfg.x}%`,
              top: `${cfg.y}%`,
              width: `${cfg.w}%`,
              transform: "translateY(-0.82em)",
              fontFamily: SERIF,
              fontSize: `${fontPx}px`,
              lineHeight: 1,
              fontWeight: cfg.bold ? 700 : 400,
              textAlign: cfg.align || "left",
              whiteSpace: "nowrap",
              color: hasVal ? "#0a0d52" : "#9ca3af",
              cursor: editMode ? "move" : "default",
              outline: isSel ? "1px dashed #E11D48" : editMode ? "1px dotted rgba(225,29,72,.35)" : "none",
              background: isSel ? "rgba(225,29,72,.08)" : "transparent",
              overflow: "visible",
            }}
          >
            {text}
          </div>
        );
      })}
    </div>
  );
}
