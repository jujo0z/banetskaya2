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
import { Printer, Loader2, RotateCcw, Layers, FlipVertical2, SeparatorHorizontal, FlaskConical } from "lucide-react";

export default function ManualDuplexDialog({ open, ids, onClose }) {
  const [busy, setBusy] = useState("");
  const [backReversed, setBackReversed] = useState(true);
  const [separators, setSeparators] = useState(false);
  const [frontDone, setFrontDone] = useState(false);
  const [from, setFrom] = useState(1);
  const [to, setTo] = useState(1);

  const total = ids?.length || 0;

  useEffect(() => {
    if (open) {
      setFrom(1);
      setTo(total || 1);
      setFrontDone(false);
    }
  }, [open, total]);

  const f = Math.max(1, Math.min(Number(from) || 1, total || 1));
  const t = Math.max(f, Math.min(Number(to) || total, total || 1));
  const rangeIds = (ids || []).slice(f - 1, t);
  const rangeCount = rangeIds.length;

  async function printSide(side) {
    if (!rangeCount) return;
    try {
      setBusy(side);
      await manualDuplexPrint(rangeIds, side, backReversed, separators);
      if (side === "front") {
        setFrontDone(true);
        toast.success(`Лицевые отправлены на печать (${rangeCount})`);
      } else {
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
      await printDuplexTest(side);
      toast.success(side === "front" ? "Пробная лицевая — на печать" : "Пробный оборот — на печать");
    } catch (e) {
      toast.error("Не удалось напечатать пробный лист");
    } finally {
      setBusy("");
    }
  }

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
            Для принтера без автоматического дуплекса. Печать в два прохода. Выбрано договоров:
            {" "}{total}. Каждый документ начинается с новой лицевой стороны.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-2">
          {/* Range */}
          <div className="border border-white/10 rounded-md p-4 bg-[#0A0A0C]/60">
            <div className="flex items-center gap-2 mb-3">
              <SeparatorHorizontal className="h-4 w-4 text-[#E11D48]" />
              <span className="font-heading text-lg">Диапазон (партия)</span>
            </div>
            <div className="flex items-end gap-3 flex-wrap">
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">Договоры с</Label>
                <Input
                  type="number" min={1} max={total}
                  className="w-24 rounded-sm bg-[#0A0A0C] border-white/10 h-9"
                  value={from}
                  onChange={(e) => setFrom(e.target.value)}
                  data-testid="duplex-range-from"
                />
              </div>
              <div className="space-y-1">
                <Label className="text-xs text-muted-foreground">по</Label>
                <Input
                  type="number" min={1} max={total}
                  className="w-24 rounded-sm bg-[#0A0A0C] border-white/10 h-9"
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                  data-testid="duplex-range-to"
                />
              </div>
              <div className="text-sm text-muted-foreground pb-2">
                будет напечатано: <b className="text-white">{rangeCount}</b> из {total}
              </div>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Дробите большие пачки на партии, чтобы удобнее переворачивать стопку.
            </p>
          </div>

          {/* Step 1 */}
          <div className="border border-white/10 rounded-md p-4 bg-[#0A0A0C]/60">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <div className="font-heading text-lg flex items-center gap-2">
                  <span className="h-6 w-6 rounded-full bg-[#E11D48] text-white text-sm flex items-center justify-center">1</span>
                  Печать лицевых сторон
                </div>
                <p className="text-sm text-muted-foreground mt-1">Страницы 1, 3, 5… выбранной партии.</p>
              </div>
              <Button
                className="rounded-sm bg-[#E11D48] hover:bg-[#BE123C] text-white"
                onClick={() => printSide("front")}
                disabled={!!busy || !rangeCount}
                data-testid="duplex-front-btn"
              >
                {busy === "front" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Printer className="h-4 w-4" />}
                Печать лицевых
              </Button>
            </div>
          </div>

          {/* Flip hint */}
          <div className="flex items-start gap-3 text-sm text-muted-foreground px-1">
            <FlipVertical2 className="h-5 w-5 text-[#E11D48] shrink-0 mt-0.5" />
            <p>
              Дождитесь окончания печати, <b className="text-white">переверните всю стопку</b> и
              вставьте обратно в лоток. Затем печатайте обороты.
            </p>
          </div>

          {/* Step 2 */}
          <div className="border border-white/10 rounded-md p-4 bg-[#0A0A0C]/60">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <div className="font-heading text-lg flex items-center gap-2">
                  <span className="h-6 w-6 rounded-full bg-[#E11D48] text-white text-sm flex items-center justify-center">2</span>
                  Печать оборотов
                </div>
                <p className="text-sm text-muted-foreground mt-1">Страницы 2, 4, 6… под перевёрнутую стопку.</p>
              </div>
              <Button
                variant="outline"
                className="rounded-sm border-white/15"
                onClick={() => printSide("back")}
                disabled={!!busy || !rangeCount}
                data-testid="duplex-back-btn"
              >
                {busy === "back" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Printer className="h-4 w-4" />}
                Печать оборотов
              </Button>
            </div>
            {!frontDone && (
              <p className="text-xs text-amber-400/80 mt-3">Сначала распечатайте лицевые стороны (шаг 1).</p>
            )}
          </div>

          {/* Options: reverse + separators */}
          <div className="space-y-2">
            <label className="flex items-center justify-between gap-4 border border-white/10 rounded-md p-3 cursor-pointer">
              <div className="flex items-center gap-2 text-sm">
                <RotateCcw className="h-4 w-4 text-muted-foreground" />
                <span>
                  Обороты в обратном порядке
                  <span className="block text-xs text-muted-foreground">
                    Оставьте включённым. Если обороты легли не на те листы — выключите и распечатайте обороты заново.
                  </span>
                </span>
              </div>
              <Switch checked={backReversed} onCheckedChange={setBackReversed} data-testid="duplex-reverse-switch" />
            </label>

            <label className="flex items-center justify-between gap-4 border border-white/10 rounded-md p-3 cursor-pointer">
              <div className="flex items-center gap-2 text-sm">
                <SeparatorHorizontal className="h-4 w-4 text-muted-foreground" />
                <span>
                  Лист-разделитель между договорами
                  <span className="block text-xs text-muted-foreground">
                    Добавляет пронумерованный лист перед каждым договором — проще разбирать пачку.
                  </span>
                </span>
              </div>
              <Switch checked={separators} onCheckedChange={setSeparators} data-testid="duplex-separators-switch" />
            </label>
          </div>

          {/* Test sheet */}
          <div className="border border-dashed border-white/15 rounded-md p-4 bg-[#0A0A0C]/40">
            <div className="flex items-center gap-2 mb-1">
              <FlaskConical className="h-4 w-4 text-[#E11D48]" />
              <span className="font-heading text-lg">Пробный лист (тест переворота)</span>
            </div>
            <p className="text-sm text-muted-foreground mb-3">
              За 10 секунд проверьте, как переворачивать лист: напечатайте лицевую, переверните лист,
              напечатайте оборот. Подсказки на самих страницах.
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
