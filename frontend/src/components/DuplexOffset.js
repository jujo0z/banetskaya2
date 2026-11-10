import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Ruler, Save, FileCheck2 } from "lucide-react";
import { getFormaBackOffset, saveFormaBackOffset, openFormaCalibration } from "@/lib/apiClient";

/** Сдвиг ОБОРОТА Форм 19/24 — компенсация смещения принтера при двусторонней печати.
 *  Значение общее (хранится на сервере) и применяется к Ф-19, Ф-24 и Полному пакету. */
export default function DuplexOffset({
  testidPrefix = "duplex",
  onSaved,
  title = "Совмещение лица и оборота",
  note = "Если при двусторонней печати оборот получается ниже лица, поднимите его. Значение общее для Ф-19, Ф-24 и пакета.",
  getFn = getFormaBackOffset,
  saveFn = saveFormaBackOffset,
  calibFn = openFormaCalibration,
  reloadKey = "",
}) {
  const [up, setUp] = useState("");
  const [right, setRight] = useState("");
  const [saving, setSaving] = useState(false);
  const [showX, setShowX] = useState(false);

  useEffect(() => {
    getFn()
      .then((d) => {
        setUp(String(d.up_mm ?? 0));
        setRight(String(d.right_mm ?? 0));
        if (Number(d.right_mm)) setShowX(true);
      })
      .catch(() => {});
  }, [reloadKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const num = (v) => {
    const n = parseFloat(String(v).replace(",", "."));
    return Number.isFinite(n) ? n : 0;
  };

  const save = async () => {
    setSaving(true);
    try {
      const d = await saveFn(num(up), num(right));
      setUp(String(d.up_mm));
      setRight(String(d.right_mm));
      toast.success(`Сдвиг оборота сохранён: вверх ${d.up_mm} мм${d.right_mm ? `, вправо ${d.right_mm} мм` : ""}`);
      onSaved && onSaved(d);
    } catch (e) {
      toast.error("Не удалось сохранить сдвиг");
    } finally {
      setSaving(false);
    }
  };

  const calib = async (apply) => {
    try {
      await calibFn(apply);
    } catch (e) {
      toast.error("Не удалось открыть лист калибровки");
    }
  };

  const step = (d) => setUp(String(Math.round((num(up) + d) * 10) / 10));

  return (
    <div className="rounded-lg border border-pink-100 bg-white/80 p-4 space-y-3" data-testid={`${testidPrefix}-back-offset`}>
      <div className="text-sm font-semibold flex items-center gap-2">
        <Ruler className="h-4 w-4 text-[#EC4899]" /> {title}
      </div>
      <p className="text-[11px] text-muted-foreground leading-snug">
        {note}
      </p>
      <div className="flex items-center gap-2">
        <span className="text-[12px] w-28 shrink-0">Поднять оборот, мм</span>
        <Button type="button" variant="outline" size="sm" onClick={() => step(-0.5)} data-testid={`${testidPrefix}-up-minus`}>−</Button>
        <Input
          value={up}
          onChange={(e) => setUp(e.target.value)}
          className="h-8 w-20 text-center"
          inputMode="decimal"
          data-testid={`${testidPrefix}-up-input`}
        />
        <Button type="button" variant="outline" size="sm" onClick={() => step(0.5)} data-testid={`${testidPrefix}-up-plus`}>+</Button>
      </div>
      {showX ? (
        <div className="flex items-center gap-2">
          <span className="text-[12px] w-28 shrink-0">Вправо, мм</span>
          <Input
            value={right}
            onChange={(e) => setRight(e.target.value)}
            className="h-8 w-20 text-center"
            inputMode="decimal"
            data-testid={`${testidPrefix}-right-input`}
          />
        </div>
      ) : (
        <button type="button" className="text-[11px] underline text-muted-foreground" onClick={() => setShowX(true)} data-testid={`${testidPrefix}-show-x`}>
          + сдвиг влево/вправо
        </button>
      )}
      <div className="text-[11px] text-muted-foreground">Отрицательное значение опускает оборот.</div>
      <div className="grid grid-cols-1 gap-2">
        <Button type="button" onClick={save} disabled={saving} className="bg-[#EC4899] hover:bg-[#DB2777]" data-testid={`${testidPrefix}-offset-save`}>
          <Save className="h-4 w-4 mr-2" /> {saving ? "Сохранение…" : "Сохранить сдвиг"}
        </Button>
        <div className="grid grid-cols-2 gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => calib(false)} data-testid={`${testidPrefix}-calib`}>
            <Ruler className="h-4 w-4 mr-1" /> Лист калибровки
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => calib(true)} data-testid={`${testidPrefix}-calib-check`}>
            <FileCheck2 className="h-4 w-4 mr-1" /> Проверка
          </Button>
        </div>
      </div>
      <p className="text-[10.5px] text-muted-foreground leading-snug">
        Как настроить: распечатайте «Лист калибровки» двусторонне (масштаб 100%), посмотрите на просвет, на какое число шкалы легла
        красная линия, и впишите это число. «Проверка» печатает лист уже с вашим сдвигом: линия должна лечь на 0.
      </p>
    </div>
  );
}
