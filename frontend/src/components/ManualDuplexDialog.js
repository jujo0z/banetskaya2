import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { manualDuplexPrint, printDuplexTest } from "@/lib/apiClient";
import { toast } from "sonner";
import {
  Printer, Loader2, RotateCcw, Layers, FlipVertical2, SeparatorHorizontal,
  FlaskConical, CheckCircle2, RefreshCw, FileText, RectangleHorizontal, RectangleVertical,
} from "lucide-react";

export default function ManualDuplexDialog({ open, ids, onClose }) {
  const [busy, setBusy] = useState("");
  const [backReversed, setBackReversed] = useState(true);
  const [separators, setSeparators] = useState(false);
  const [orientation, setOrientation] = useState("portrait"); // portrait | landscape
  const [from, setFrom] = useState(1);
  const [to, setTo] = useState(1);
  const [stage, setStage] = useState("front"); // front | flip | done

  const total = ids?.length || 0;

  useEffect(() => {
    if (open) {
      setFrom(1);
      setTo(total || 1);
      setStage("front");
      setBusy("");
    }
  }, [open, total]);

  const f = Math.max(1, Math.min(Number(from) || 1, total || 1));
  const t = Math.max(f, Math.min(Number(to) || total, total || 1));
  const rangeIds = (ids || []).slice(f - 1, t);
  const rangeCount = rangeIds.length;
  const locked = stage !== "front"; // options fixed once printing started

  async function printSide(side) {
    if (!rangeCount) return;
    try {
      setBusy(side);
      await manualDuplexPrint(rangeIds, side, backReversed, separators, orientation);
      if (side === "front") {
        setStage("flip");
        toast.success(`Лицевые отправлены на печать (${rangeCount})`);
      } else {
        setStage("done");
        toast.success(`Обороты отправлены на печать (${rangeCount})`);
      }
    } catch (e) {
      toast.error("Не удалось отправить на печать");
    } finally {
      setBusy("");
    }
  }

  async function printTest(side) {
    try {
      setBusy("test-" + side);
      await printDuplexTest(side, orientation);
      toast.success(side === "front" ? "Пробная лицевая — на печать" : "Пробный оборот — на печать");
    } catch (e) {
      toast.error("Не удалось напечатать пробный лист");
    } finally {
      setBusy("");
    }
  }

  function nextBatch() {
    const nextFrom = t + 1;
    if (nextFrom > total) {
      toast.info("Все договоры напечатаны");
      onClose();
      return;
    }
    setFrom(nextFrom);
    setTo(total);
    setStage("front");
  }

  function restart() {
    setFrom(1);
    setTo(total);
    setStage("front");
  }

  const orientOptions = [
    { value: "portrait", icon: RectangleVertical, label: "Книжная (обычная)" },
    { value: "landscape", icon: RectangleHorizontal, label: "Альбомная" },
  ];

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent
        className="max-w-2xl max-h-[92vh] overflow-y-auto rounded-lg bg-card border-white/10"
        data-testid="manual-duplex-dialog"
      >
        <DialogHeader>
          <DialogTitle className="font-heading text-3xl tracking-tight flex items-center gap-2">
            <Layers className="h-6 w-6 text-[#E11D48]" /> Двусторонняя печать вручную
          </DialogTitle>
          <DialogDescription>
            Для принтера без автодуплекса. Печать в два прохода. Выбрано договоров: {total}.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-2">
          {/* Options */}
          <div className="border border-white/10 rounded-md p-4 bg-[#0A0A0C]/60 space-y-4">
            {/* Range */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <SeparatorHorizontal className="h-4 w-4 text-[#E11D48]" />
                <span className="font-heading text-base">Диапазон (партия)</span>
              </div>
              <div className="flex items-end gap-3 flex-wrap">
                <div className="space-y-1">
                  <Label className="text-xs text-muted-foreground">Договоры с</Label>
                  <Input
                    type="number" min={1} max={total} disabled={locked}
                    className="w-24 rounded-sm bg-[#0A0A0C] border-white/10 h-9"
                    value={from} onChange={(e) => setFrom(e.target.value)}
                    data-testid="duplex-range-from"
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-muted-foreground">по</Label>
                  <Input
                    type="number" min={1} max={total} disabled={locked}
                    className="w-24 rounded-sm bg-[#0A0A0C] border-white/10 h-9"
                    value={to} onChange={(e) => setTo(e.target.value)}
                    data-testid="duplex-range-to"
                  />
                </div>
                <div className="text-sm text-muted-foreground pb-2">
                  в партии: <b className="text-white">{rangeCount}</b> из {total}
                </div>
              </div>
            </div>

            {/* Orientation */}
            <div>
              <div className="flex items-center gap-2 mb-2">
                <FileText className="h-4 w-4 text-[#E11D48]" />
                <span className="font-heading text-base">Ориентация</span>
              </div>
              <div className="flex gap-2">
                {orientOptions.map(({ value, icon: Icon, label }) => (
                  <button
                    key={value}
                    type="button"
                    disabled={locked}
                    onClick={() => setOrientation(value)}
                    className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-sm text-sm transition-colors border ${
                      orientation === value
                        ? "bg-[#E11D48] text-white border-[#E11D48]"
                        : "border-white/15 text-muted-foreground hover:text-white"
                    } ${locked ? "opacity-50 cursor-not-allowed" : ""}`}
                    data-testid={`duplex-orient-${value}`}
                  >
                    <Icon className="h-4 w-4" /> {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Toggles */}
            <label className="flex items-center justify-between gap-4 cursor-pointer">
              <div className="flex items-center gap-2 text-sm">
                <SeparatorHorizontal className="h-4 w-4 text-muted-foreground" />
                <span>
                  Лист-разделитель между договорами
                  <span className="block text-xs text-muted-foreground">
                    Пронумерованный лист перед каждым договором — проще разбирать пачку.
                  </span>
                </span>
              </div>
              <Switch checked={separators} onCheckedChange={setSeparators} disabled={locked} data-testid="duplex-separators-switch" />
            </label>

            <label className="flex items-center justify-between gap-4 cursor-pointer">
              <div className="flex items-center gap-2 text-sm">
                <RotateCcw className="h-4 w-4 text-muted-foreground" />
                <span>
                  Обороты в обратном порядке
                  <span className="block text-xs text-muted-foreground">
                    Оставьте включённым. Если обороты легли не на те листы — выключите и печатайте обороты заново.
                  </span>
                </span>
              </div>
              <Switch checked={backReversed} onCheckedChange={setBackReversed} disabled={locked} data-testid="duplex-reverse-switch" />
            </label>
          </div>

          {/* Guided stepper */}
          {stage === "front" && (
            <div className="border border-[#E11D48]/40 rounded-md p-5 bg-[#E11D48]/5" data-testid="duplex-stage-front">
              <div className="font-heading text-lg flex items-center gap-2 mb-1">
                <span className="h-6 w-6 rounded-full bg-[#E11D48] text-white text-sm flex items-center justify-center">1</span>
                Шаг 1. Печать лицевых сторон
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                Страницы 1, 3, 5… партии. Дождитесь, пока принтер напечатает и остановится.
              </p>
              <Button
                className="w-full rounded-sm bg-[#E11D48] hover:bg-[#BE123C] text-white h-11 text-base"
                onClick={() => printSide("front")}
                disabled={!!busy || !rangeCount}
                data-testid="duplex-front-btn"
              >
                {busy === "front" ? <Loader2 className="h-5 w-5 animate-spin" /> : <Printer className="h-5 w-5" />}
                Печать лицевых ({rangeCount})
              </Button>
            </div>
          )}

          {stage === "flip" && (
            <div className="border border-amber-500/40 rounded-md p-5 bg-amber-500/5" data-testid="duplex-stage-flip">
              <div className="flex items-center gap-3 mb-2">
                <FlipVertical2 className="h-8 w-8 text-amber-400 shrink-0" />
                <div className="font-heading text-xl">Переверните стопку</div>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                Принтер остановился? Возьмите <b className="text-white">всю распечатанную стопку</b>,
                переверните её и вставьте обратно в лоток. Затем печатайте обороты.
              </p>
              <div className="flex flex-col sm:flex-row gap-2">
                <Button
                  className="flex-1 rounded-sm bg-[#E11D48] hover:bg-[#BE123C] text-white h-11 text-base"
                  onClick={() => printSide("back")}
                  disabled={!!busy}
                  data-testid="duplex-back-btn"
                >
                  {busy === "back" ? <Loader2 className="h-5 w-5 animate-spin" /> : <Printer className="h-5 w-5" />}
                  Шаг 2. Печать оборотов ({rangeCount})
                </Button>
                <Button
                  variant="outline" className="rounded-sm border-white/15"
                  onClick={() => setStage("front")} disabled={!!busy}
                  data-testid="duplex-reprint-front-btn"
                >
                  <RefreshCw className="h-4 w-4" /> Перепечатать лицевые
                </Button>
              </div>
            </div>
          )}

          {stage === "done" && (
            <div className="border border-emerald-500/40 rounded-md p-5 bg-emerald-500/5" data-testid="duplex-stage-done">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle2 className="h-8 w-8 text-emerald-400 shrink-0" />
                <div className="font-heading text-xl">Партия напечатана</div>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                Договоры {f}–{t} готовы. Если обороты легли не на те листы — включите/выключите
                «Обороты в обратном порядке» и распечатайте обороты заново.
              </p>
              <div className="flex flex-col sm:flex-row gap-2">
                {t < total ? (
                  <Button
                    className="flex-1 rounded-sm bg-[#E11D48] hover:bg-[#BE123C] text-white"
                    onClick={nextBatch}
                    data-testid="duplex-next-batch-btn"
                  >
                    <Printer className="h-4 w-4" /> Следующая партия ({t + 1}–{total})
                  </Button>
                ) : (
                  <Button
                    className="flex-1 rounded-sm bg-emerald-600 hover:bg-emerald-700 text-white"
                    onClick={onClose}
                    data-testid="duplex-finish-btn"
                  >
                    <CheckCircle2 className="h-4 w-4" /> Готово, закрыть
                  </Button>
                )}
                <Button
                  variant="outline" className="rounded-sm border-white/15"
                  onClick={restart}
                  data-testid="duplex-restart-btn"
                >
                  <RotateCcw className="h-4 w-4" /> Начать заново
                </Button>
              </div>
            </div>
          )}

          {/* Test sheet */}
          <div className="border border-dashed border-white/15 rounded-md p-4 bg-[#0A0A0C]/40">
            <div className="flex items-center gap-2 mb-1">
              <FlaskConical className="h-4 w-4 text-[#E11D48]" />
              <span className="font-heading text-base">Пробный лист (тест переворота)</span>
            </div>
            <p className="text-sm text-muted-foreground mb-3">
              За 10 секунд подберите переворот: напечатайте лицевую, переверните лист, напечатайте оборот.
              Учитывает выбранную ориентацию. Подсказки — на самих страницах.
            </p>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline" className="rounded-sm border-white/15"
                onClick={() => printTest("front")} disabled={!!busy}
                data-testid="duplex-test-front-btn"
              >
                {busy === "test-front" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Printer className="h-4 w-4" />}
                Пробная лицевая
              </Button>
              <Button
                variant="outline" className="rounded-sm border-white/15"
                onClick={() => printTest("back")} disabled={!!busy}
                data-testid="duplex-test-back-btn"
              >
                {busy === "test-back" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Printer className="h-4 w-4" />}
                Пробный оборот
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
