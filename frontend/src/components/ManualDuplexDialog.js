import { useState, useEffect } from "react";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
  DropdownMenuLabel, DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  manualDuplexPrint, printDuplexTest, getTemplateInfo,
  getPrintProfiles, savePrintProfile, deletePrintProfile,
} from "@/lib/apiClient";
import { toast } from "sonner";
import {
  Printer, Loader2, RotateCcw, Layers, FlipVertical2, SeparatorHorizontal, FlaskConical,
  CheckCircle2, RefreshCw, FileText, RectangleHorizontal, RectangleVertical,
  BookOpen, BookmarkPlus, Bookmark, Trash2, Files,
} from "lucide-react";

export default function ManualDuplexDialog({ open, ids, onClose }) {
  const [busy, setBusy] = useState("");
  const [backReversed, setBackReversed] = useState(true);
  const [separators, setSeparators] = useState(false);
  const [orientation, setOrientation] = useState("portrait");
  const [flipEdge, setFlipEdge] = useState("long");
  const [from, setFrom] = useState(1);
  const [to, setTo] = useState(1);
  const [stage, setStage] = useState("front");
  const [pagesPerDoc, setPagesPerDoc] = useState(2);
  const [profiles, setProfiles] = useState([]);
  const [profileName, setProfileName] = useState("");
  const [saveOpen, setSaveOpen] = useState(false);

  const total = ids?.length || 0;

  useEffect(() => {
    if (open) {
      setFrom(1); setTo(total || 1); setStage("front"); setBusy("");
      getTemplateInfo().then((d) => setPagesPerDoc(d.pages_per_doc || 2)).catch(() => {});
      getPrintProfiles().then(setProfiles).catch(() => {});
    }
  }, [open, total]);

  const f = Math.max(1, Math.min(Number(from) || 1, total || 1));
  const t = Math.max(f, Math.min(Number(to) || total, total || 1));
  const rangeIds = (ids || []).slice(f - 1, t);
  const rangeCount = rangeIds.length;
  const locked = stage !== "front";

  const sheetsPerDoc = Math.ceil(pagesPerDoc / 2);
  const sheets = rangeCount * sheetsPerDoc + (separators ? rangeCount : 0);

  async function printSide(side) {
    if (!rangeCount) return;
    try {
      setBusy(side);
      await manualDuplexPrint(rangeIds, side, backReversed, separators, orientation, flipEdge);
      setStage(side === "front" ? "flip" : "done");
      toast.success(side === "front" ? `Лицевые на печать (${rangeCount})` : `Обороты на печать (${rangeCount})`);
    } catch (e) {
      toast.error("Не удалось отправить на печать");
    } finally { setBusy(""); }
  }

  async function printTest(side) {
    try {
      setBusy("test-" + side);
      await printDuplexTest(side, orientation);
      toast.success("Пробный лист — на печать");
    } catch (e) { toast.error("Не удалось напечатать пробный лист"); }
    finally { setBusy(""); }
  }

  function applyProfile(p) {
    const s = p.settings || {};
    setOrientation(s.orientation === "landscape" ? "landscape" : "portrait");
    setFlipEdge(s.flipEdge === "short" ? "short" : "long");
    setBackReversed(s.backReversed !== false);
    setSeparators(!!s.separators);
    toast.success(`Профиль «${p.name}» применён`);
  }

  async function handleSaveProfile() {
    const name = profileName.trim();
    if (!name) return;
    try {
      const p = await savePrintProfile(name, { orientation, flipEdge, backReversed, separators });
      setProfiles((prev) => [p, ...prev]);
      setProfileName(""); setSaveOpen(false);
      toast.success("Профиль сохранён");
    } catch { toast.error("Не удалось сохранить профиль"); }
  }

  async function handleDeleteProfile(id, e) {
    e.stopPropagation();
    try { await deletePrintProfile(id); setProfiles((prev) => prev.filter((p) => p.id !== id)); }
    catch { toast.error("Не удалось удалить профиль"); }
  }

  function nextBatch() {
    if (t >= total) { onClose(); return; }
    setFrom(t + 1); setTo(total); setStage("front");
  }

  const seg = (val, cur, set, icon, label, tid) => {
    const Icon = icon;
    return (
      <button type="button" disabled={locked} onClick={() => set(val)}
        className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-sm text-sm border transition-colors ${
          cur === val ? "bg-[#E11D48] text-white border-[#E11D48]" : "border-white/15 text-muted-foreground hover:text-white"
        } ${locked ? "opacity-50 cursor-not-allowed" : ""}`} data-testid={tid}>
        <Icon className="h-4 w-4" /> {label}
      </button>
    );
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-2xl max-h-[92vh] overflow-y-auto rounded-lg bg-card border-white/10" data-testid="manual-duplex-dialog">
        <DialogHeader>
          <DialogTitle className="font-heading text-3xl tracking-tight flex items-center gap-2">
            <Layers className="h-6 w-6 text-[#E11D48]" /> Двусторонняя печать вручную
          </DialogTitle>
          <DialogDescription>
            Для принтера без автодуплекса. Печать в два прохода. Выбрано договоров: {total}.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-2">
          {/* Profiles bar */}
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" className="rounded-sm border-white/15" data-testid="duplex-profiles-btn">
                  <Bookmark className="h-4 w-4" /> Профили принтера
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-72">
                <DropdownMenuLabel>Загрузить настройки</DropdownMenuLabel>
                <DropdownMenuSeparator />
                {profiles.length === 0 && <div className="px-2 py-3 text-sm text-muted-foreground">Профилей пока нет</div>}
                {profiles.map((p) => (
                  <DropdownMenuItem key={p.id} onClick={() => applyProfile(p)} className="flex items-center justify-between gap-2" data-testid={`duplex-profile-${p.id}`}>
                    <span className="truncate">{p.name}</span>
                    <button onClick={(e) => handleDeleteProfile(p.id, e)} className="text-muted-foreground hover:text-[#FF3B30]"><Trash2 className="h-3.5 w-3.5" /></button>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
            <Popover open={saveOpen} onOpenChange={setSaveOpen}>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm" className="rounded-sm border-white/15" data-testid="duplex-profile-save-btn">
                  <BookmarkPlus className="h-4 w-4" /> Сохранить профиль
                </Button>
              </PopoverTrigger>
              <PopoverContent align="end" className="w-72">
                <p className="text-sm font-medium mb-2">Сохранить текущие настройки</p>
                <Input className="rounded-sm mb-2" placeholder="Напр. HP LaserJet" value={profileName} onChange={(e) => setProfileName(e.target.value)} data-testid="duplex-profile-name" />
                <Button className="w-full rounded-sm bg-[#E11D48] hover:bg-[#BE123C] text-white" onClick={handleSaveProfile} disabled={!profileName.trim()} data-testid="duplex-profile-save-confirm">Сохранить</Button>
              </PopoverContent>
            </Popover>
          </div>

          {/* Options */}
          <div className="border border-white/10 rounded-md p-4 bg-[#0A0A0C]/60 space-y-4">
            <div>
              <div className="flex items-center gap-2 mb-2"><SeparatorHorizontal className="h-4 w-4 text-[#E11D48]" /><span className="font-heading text-base">Диапазон (партия)</span></div>
              <div className="flex items-end gap-3 flex-wrap">
                <div className="space-y-1"><Label className="text-xs text-muted-foreground">Договоры с</Label>
                  <Input type="number" min={1} max={total} disabled={locked} className="w-24 rounded-sm bg-[#0A0A0C] border-white/10 h-9" value={from} onChange={(e) => setFrom(e.target.value)} data-testid="duplex-range-from" /></div>
                <div className="space-y-1"><Label className="text-xs text-muted-foreground">по</Label>
                  <Input type="number" min={1} max={total} disabled={locked} className="w-24 rounded-sm bg-[#0A0A0C] border-white/10 h-9" value={to} onChange={(e) => setTo(e.target.value)} data-testid="duplex-range-to" /></div>
                <div className="text-sm text-muted-foreground pb-2">в партии: <b className="text-white">{rangeCount}</b> из {total}</div>
              </div>
              <div className="flex items-center gap-2 mt-2 text-sm text-[#E11D48]" data-testid="duplex-paper-estimate">
                <Files className="h-4 w-4" /> Потребуется бумаги: <b>≈ {sheets}</b> {sheets === 1 ? "лист" : "листов"}
                <span className="text-muted-foreground text-xs">({sheetsPerDoc} на договор{separators ? " + 1 разделитель" : ""})</span>
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-2"><FileText className="h-4 w-4 text-[#E11D48]" /><span className="font-heading text-base">Ориентация</span></div>
              <div className="flex gap-2">
                {seg("portrait", orientation, setOrientation, RectangleVertical, "Книжная (обычная)", "duplex-orient-portrait")}
                {seg("landscape", orientation, setOrientation, RectangleHorizontal, "Альбомная", "duplex-orient-landscape")}
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-2"><BookOpen className="h-4 w-4 text-[#E11D48]" /><span className="font-heading text-base">Переворот стопки</span></div>
              <div className="flex gap-2">
                {seg("long", flipEdge, setFlipEdge, RectangleVertical, "По длинному краю", "duplex-flip-long")}
                {seg("short", flipEdge, setFlipEdge, RectangleHorizontal, "По короткому краю", "duplex-flip-short")}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Короткий край переворачивает обороты на 180°, чтобы не были вверх ногами.</p>
            </div>

            <label className="flex items-center justify-between gap-4 cursor-pointer">
              <div className="flex items-center gap-2 text-sm"><SeparatorHorizontal className="h-4 w-4 text-muted-foreground" />
                <span>Лист-разделитель между договорами<span className="block text-xs text-muted-foreground">Пронумерованный лист перед каждым договором.</span></span></div>
              <Switch checked={separators} onCheckedChange={setSeparators} disabled={locked} data-testid="duplex-separators-switch" />
            </label>
            <label className="flex items-center justify-between gap-4 cursor-pointer">
              <div className="flex items-center gap-2 text-sm"><RotateCcw className="h-4 w-4 text-muted-foreground" />
                <span>Обороты в обратном порядке<span className="block text-xs text-muted-foreground">Если легли не на те листы — переключите и печатайте обороты заново.</span></span></div>
              <Switch checked={backReversed} onCheckedChange={setBackReversed} disabled={locked} data-testid="duplex-reverse-switch" />
            </label>
          </div>

          {/* Stepper */}
          {stage === "front" && (
            <div className="border border-[#E11D48]/40 rounded-md p-5 bg-[#E11D48]/5" data-testid="duplex-stage-front">
              <div className="font-heading text-lg flex items-center gap-2 mb-1"><span className="h-6 w-6 rounded-full bg-[#E11D48] text-white text-sm flex items-center justify-center">1</span>Шаг 1. Печать лицевых</div>
              <p className="text-sm text-muted-foreground mb-4">Дождитесь, пока принтер напечатает и остановится.</p>
              <Button className="w-full rounded-sm bg-[#E11D48] hover:bg-[#BE123C] text-white h-11 text-base" onClick={() => printSide("front")} disabled={!!busy || !rangeCount} data-testid="duplex-front-btn">
                {busy === "front" ? <Loader2 className="h-5 w-5 animate-spin" /> : <Printer className="h-5 w-5" />} Печать лицевых ({rangeCount})
              </Button>
            </div>
          )}
          {stage === "flip" && (
            <div className="border border-amber-500/40 rounded-md p-5 bg-amber-500/5" data-testid="duplex-stage-flip">
              <div className="flex items-center gap-3 mb-2"><FlipVertical2 className="h-8 w-8 text-amber-400 shrink-0" /><div className="font-heading text-xl">Переверните стопку</div></div>
              <p className="text-sm text-muted-foreground mb-4">Принтер остановился? Переверните <b className="text-white">всю стопку</b> и вставьте обратно. Затем печатайте обороты.</p>
              <div className="flex flex-col sm:flex-row gap-2">
                <Button className="flex-1 rounded-sm bg-[#E11D48] hover:bg-[#BE123C] text-white h-11 text-base" onClick={() => printSide("back")} disabled={!!busy} data-testid="duplex-back-btn">
                  {busy === "back" ? <Loader2 className="h-5 w-5 animate-spin" /> : <Printer className="h-5 w-5" />} Шаг 2. Печать оборотов ({rangeCount})
                </Button>
                <Button variant="outline" className="rounded-sm border-white/15" onClick={() => setStage("front")} disabled={!!busy} data-testid="duplex-reprint-front-btn"><RefreshCw className="h-4 w-4" /> Перепечатать лицевые</Button>
              </div>
            </div>
          )}
          {stage === "done" && (
            <div className="border border-emerald-500/40 rounded-md p-5 bg-emerald-500/5" data-testid="duplex-stage-done">
              <div className="flex items-center gap-3 mb-2"><CheckCircle2 className="h-8 w-8 text-emerald-400 shrink-0" /><div className="font-heading text-xl">Партия напечатана</div></div>
              <p className="text-sm text-muted-foreground mb-4">Договоры {f}–{t} готовы.</p>
              <div className="flex flex-col sm:flex-row gap-2">
                {t < total ? (
                  <Button className="flex-1 rounded-sm bg-[#E11D48] hover:bg-[#BE123C] text-white" onClick={nextBatch} data-testid="duplex-next-batch-btn"><Printer className="h-4 w-4" /> Следующая партия ({t + 1}–{total})</Button>
                ) : (
                  <Button className="flex-1 rounded-sm bg-emerald-600 hover:bg-emerald-700 text-white" onClick={onClose} data-testid="duplex-finish-btn"><CheckCircle2 className="h-4 w-4" /> Готово, закрыть</Button>
                )}
                <Button variant="outline" className="rounded-sm border-white/15" onClick={() => { setFrom(1); setTo(total); setStage("front"); }} data-testid="duplex-restart-btn"><RotateCcw className="h-4 w-4" /> Начать заново</Button>
              </div>
            </div>
          )}

          {/* Test */}
          <div className="border border-dashed border-white/15 rounded-md p-4 bg-[#0A0A0C]/40">
            <div className="flex items-center gap-2 mb-1"><FlaskConical className="h-4 w-4 text-[#E11D48]" /><span className="font-heading text-base">Пробный лист (тест переворота)</span></div>
            <p className="text-sm text-muted-foreground mb-3">Учитывает ориентацию. Напечатайте лицевую, переверните лист, напечатайте оборот.</p>
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" className="rounded-sm border-white/15" onClick={() => printTest("front")} disabled={!!busy} data-testid="duplex-test-front-btn">
                {busy === "test-front" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Printer className="h-4 w-4" />} Пробная лицевая</Button>
              <Button variant="outline" className="rounded-sm border-white/15" onClick={() => printTest("back")} disabled={!!busy} data-testid="duplex-test-back-btn">
                {busy === "test-back" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Printer className="h-4 w-4" />} Пробный оборот</Button>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
