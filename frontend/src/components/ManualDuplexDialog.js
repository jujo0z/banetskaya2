import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { manualDuplexPrint } from "@/lib/apiClient";
import { toast } from "sonner";
import { Printer, Loader2, RotateCcw, Layers, FlipVertical2 } from "lucide-react";

export default function ManualDuplexDialog({ open, ids, onClose }) {
  const [busy, setBusy] = useState("");
  const [backReversed, setBackReversed] = useState(true);
  const [frontDone, setFrontDone] = useState(false);

  const count = ids?.length || 0;

  async function printSide(side) {
    if (!count) return;
    try {
      setBusy(side);
      await manualDuplexPrint(ids, side, backReversed);
      if (side === "front") {
        setFrontDone(true);
        toast.success("Лицевые страницы отправлены на печать");
      } else {
        toast.success("Обороты отправлены на печать");
      }
    } catch (e) {
      toast.error("Не удалось отправить на печать");
    } finally {
      setBusy("");
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent
        className="max-w-2xl rounded-lg bg-card border-white/10"
        data-testid="manual-duplex-dialog"
      >
        <DialogHeader>
          <DialogTitle className="font-heading text-3xl tracking-tight flex items-center gap-2">
            <Layers className="h-6 w-6 text-[#E11D48]" /> Двусторонняя печать вручную
          </DialogTitle>
          <DialogDescription>
            Для принтера без автоматической двусторонней печати. Печатаем всю пачку
            ({count} {count === 1 ? "договор" : "договоров"}) в два прохода. Каждый документ
            автоматически начинается с новой лицевой стороны.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-2">
          {/* Step 1 */}
          <div className="border border-white/10 rounded-md p-4 bg-[#0A0A0C]/60">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <div className="font-heading text-lg flex items-center gap-2">
                  <span className="h-6 w-6 rounded-full bg-[#E11D48] text-white text-sm flex items-center justify-center">1</span>
                  Печать лицевых сторон
                </div>
                <p className="text-sm text-muted-foreground mt-1">
                  Печатает страницы 1, 3, 5… всех выбранных договоров.
                </p>
              </div>
              <Button
                className="rounded-sm bg-[#E11D48] hover:bg-[#BE123C] text-white"
                onClick={() => printSide("front")}
                disabled={!!busy || !count}
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
              вставьте обратно в лоток чистой стороной для печати. Затем печатайте обороты.
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
                <p className="text-sm text-muted-foreground mt-1">
                  Печатает страницы 2, 4, 6… в порядке, соответствующем перевёрнутой стопке.
                </p>
              </div>
              <Button
                variant="outline"
                className="rounded-sm border-white/15"
                onClick={() => printSide("back")}
                disabled={!!busy || !count}
                data-testid="duplex-back-btn"
              >
                {busy === "back" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Printer className="h-4 w-4" />}
                Печать оборотов
              </Button>
            </div>
            {!frontDone && (
              <p className="text-xs text-amber-400/80 mt-3">
                Сначала распечатайте лицевые стороны (шаг 1).
              </p>
            )}
          </div>

          {/* Back order toggle */}
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
            <Switch
              checked={backReversed}
              onCheckedChange={setBackReversed}
              data-testid="duplex-reverse-switch"
            />
          </label>
        </div>
      </DialogContent>
    </Dialog>
  );
}
