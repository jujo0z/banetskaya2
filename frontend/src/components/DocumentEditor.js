import { useState, useEffect, useRef, useCallback } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from "@/components/ui/accordion";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { FIELDS, FIELD_GROUPS, FIELD_MAP, SECTIONS } from "@/lib/fields";
import {
  saveContract,
  updateContract,
  previewPdfUrl,
  downloadPreview,
  getPresets,
  savePreset,
  deletePreset,
} from "@/lib/apiClient";
import { toast } from "sonner";
import {
  FileText, FileType, Printer, Save, Loader2, Eye, RefreshCw, ExternalLink,
  FileSignature, User, Home, BookUser, PlusCircle, SlidersHorizontal,
  BookmarkPlus, Bookmark, Trash2, FileClock,
} from "lucide-react";

const GROUP_ICONS = { FileSignature, User, Home, BookUser, PlusCircle };

export default function DocumentEditor({
  open,
  initial,
  contractId = null,
  initialStatus = "final",
  onClose,
  onSaved,
}) {
  const [fields, setFields] = useState(initial || {});
  const [savedId, setSavedId] = useState(contractId);
  const [status, setStatus] = useState(initialStatus);
  const [busy, setBusy] = useState("");
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewing, setPreviewing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [presets, setPresets] = useState([]);
  const [presetName, setPresetName] = useState("");
  const [presetOpen, setPresetOpen] = useState(false);

  const urlRef = useRef(null);
  const editedRef = useRef(false);
  const [tracker, setTracker] = useState(initial);

  // Re-init state whenever a new subject is opened
  if (initial !== tracker) {
    setTracker(initial);
    setFields(initial || {});
    setSavedId(contractId);
    setStatus(initialStatus);
    editedRef.current = false;
  }

  const update = (key, value) => {
    editedRef.current = true;
    setFields((prev) => ({ ...prev, [key]: value }));
  };

  const revokeUrl = () => {
    if (urlRef.current) {
      window.URL.revokeObjectURL(urlRef.current);
      urlRef.current = null;
    }
  };

  const refreshPreview = useCallback(async (data) => {
    setPreviewing(true);
    try {
      const url = await previewPdfUrl(data);
      revokeUrl();
      urlRef.current = url;
      setPreviewUrl(url);
    } catch (e) {
      toast.error("Не удалось обновить просмотр");
    } finally {
      setPreviewing(false);
    }
  }, []);

  // Load presets + first preview on open
  useEffect(() => {
    if (!open) return;
    editedRef.current = false;
    getPresets().then(setPresets).catch(() => {});
    refreshPreview(initial || {});
    // eslint-disable-next-line
  }, [open, initial]);

  // Debounced auto-refresh — only after an actual user edit (avoids double render on open)
  useEffect(() => {
    if (!open || !autoRefresh || !editedRef.current) return;
    const t = setTimeout(() => refreshPreview(fields), 1400);
    return () => clearTimeout(t);
    // eslint-disable-next-line
  }, [fields, autoRefresh, open]);

  useEffect(() => () => revokeUrl(), []);

  async function persist(newStatus) {
    const st = newStatus || status;
    let res;
    if (savedId) {
      res = await updateContract(savedId, fields, st);
    } else {
      res = await saveContract(fields, st);
      setSavedId(res.id);
    }
    setStatus(st);
    onSaved && onSaved();
    return res;
  }

  async function handleSave(newStatus, key) {
    try {
      setBusy(key);
      await persist(newStatus);
      toast.success(newStatus === "draft" ? "Черновик сохранён" : "Договор сохранён в историю");
    } catch (e) {
      toast.error("Не удалось сохранить");
    } finally {
      setBusy("");
    }
  }

  async function handleDownload(format) {
    try {
      setBusy(format);
      await downloadPreview(fields, format, `Договор.${format}`);
      toast.success(format === "pdf" ? "PDF готов" : "Word-документ готов");
    } catch (e) {
      toast.error("Ошибка при формировании документа");
    } finally {
      setBusy("");
    }
  }

  async function handlePrint() {
    try {
      setBusy("print");
      const url = await previewPdfUrl(fields);
      const w = window.open(url);
      if (w) w.onload = () => w.print();
    } catch (e) {
      toast.error("Не удалось открыть для печати");
    } finally {
      setBusy("");
    }
  }

  function applyPreset(p) {
    editedRef.current = true;
    setFields((prev) => ({ ...prev, ...p.fields }));
    toast.success(`Пресет «${p.name}» применён`);
  }

  async function handleSavePreset() {
    const name = presetName.trim();
    if (!name) return;
    try {
      const p = await savePreset(name, fields);
      setPresets((prev) => [p, ...prev]);
      setPresetName("");
      setPresetOpen(false);
      toast.success("Пресет сохранён");
    } catch (e) {
      toast.error("Не удалось сохранить пресет");
    }
  }

  async function handleDeletePreset(id, e) {
    e.stopPropagation();
    try {
      await deletePreset(id);
      setPresets((prev) => prev.filter((p) => p.id !== id));
    } catch (e2) {
      toast.error("Не удалось удалить пресет");
    }
  }

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent
        className="max-w-[1400px] w-[97vw] max-h-[94vh] p-0 gap-0 overflow-hidden rounded-lg bg-card border-white/10"
        data-testid="document-editor"
      >
        {/* Header */}
        <DialogHeader className="px-6 py-4 border-b border-white/10 bg-gradient-to-r from-[#E11D48]/10 via-transparent to-transparent">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-3">
              <DialogTitle className="font-heading text-3xl tracking-tight">
                Редактор договора
              </DialogTitle>
              <Badge
                className={`rounded-full border-0 ${
                  status === "draft"
                    ? "bg-amber-500/15 text-amber-400"
                    : "bg-emerald-500/15 text-emerald-400"
                }`}
                data-testid="editor-status-badge"
              >
                {status === "draft" ? (
                  <><FileClock className="h-3 w-3 mr-1" /> Черновик</>
                ) : (
                  <>Готов</>
                )}
              </Badge>
            </div>
            <div className="flex items-center gap-2">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="rounded-sm border-white/15" data-testid="preset-apply-btn">
                    <Bookmark className="h-4 w-4" /> Пресеты
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-72">
                  <DropdownMenuLabel>Применить пресет</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {presets.length === 0 && (
                    <div className="px-2 py-3 text-sm text-muted-foreground">Пресетов пока нет</div>
                  )}
                  {presets.map((p) => (
                    <DropdownMenuItem
                      key={p.id}
                      onClick={() => applyPreset(p)}
                      className="flex items-center justify-between gap-2"
                      data-testid={`preset-item-${p.id}`}
                    >
                      <span className="truncate">{p.name}</span>
                      <button
                        onClick={(e) => handleDeletePreset(p.id, e)}
                        className="text-muted-foreground hover:text-[#FF3B30]"
                        title="Удалить пресет"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>

              <Popover open={presetOpen} onOpenChange={setPresetOpen}>
                <PopoverTrigger asChild>
                  <Button variant="outline" size="sm" className="rounded-sm border-white/15" data-testid="preset-save-btn">
                    <BookmarkPlus className="h-4 w-4" /> Сохранить пресет
                  </Button>
                </PopoverTrigger>
                <PopoverContent align="end" className="w-72">
                  <p className="text-sm font-medium mb-2">Новый пресет из текущих полей</p>
                  <Input
                    className="rounded-sm mb-2"
                    placeholder="Название пресета"
                    value={presetName}
                    onChange={(e) => setPresetName(e.target.value)}
                    data-testid="preset-name-input"
                  />
                  <Button
                    className="w-full rounded-sm bg-[#E11D48] hover:bg-[#BE123C] text-white"
                    onClick={handleSavePreset}
                    disabled={!presetName.trim()}
                    data-testid="preset-save-confirm"
                  >
                    Сохранить
                  </Button>
                </PopoverContent>
              </Popover>
            </div>
          </div>
          <DialogDescription className="sr-only">
            Редактирование полей договора с живым предпросмотром PDF.
          </DialogDescription>
        </DialogHeader>

        {/* Body: two panes */}
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.05fr)] min-h-0">
          {/* Left: editor */}
          <div className="overflow-y-auto max-h-[62vh] lg:max-h-[74vh] px-6 py-5 border-b lg:border-b-0 lg:border-r border-white/10">
            <Accordion type="multiple" defaultValue={["contract", "tenant", "sections"]} className="space-y-3">
              {FIELD_GROUPS.map((g) => {
                const Icon = GROUP_ICONS[g.icon] || FileText;
                return (
                  <AccordionItem
                    key={g.id}
                    value={g.id}
                    className="border border-white/10 rounded-md bg-[#0A0A0C]/60 px-4"
                  >
                    <AccordionTrigger className="hover:no-underline py-3" data-testid={`group-${g.id}`}>
                      <span className="flex items-center gap-2.5 text-base font-heading">
                        <Icon className="h-4 w-4 text-[#E11D48]" /> {g.title}
                      </span>
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pb-2">
                        {g.keys.map((key) => (
                          <div key={key} className="space-y-1.5">
                            <Label className="text-[11px] uppercase tracking-[0.08em] text-muted-foreground">
                              {FIELD_MAP[key] || key}
                            </Label>
                            <Input
                              className="rounded-sm bg-[#0A0A0C] border-white/10 focus:border-[#E11D48] h-9"
                              value={fields[key] || ""}
                              onChange={(e) => update(key, e.target.value)}
                              data-testid={`field-${key}`}
                            />
                          </div>
                        ))}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                );
              })}

              {/* Moderation / clause editor */}
              <AccordionItem value="sections" className="border border-white/10 rounded-md bg-[#0A0A0C]/60 px-4">
                <AccordionTrigger className="hover:no-underline py-3" data-testid="group-sections">
                  <span className="flex items-center gap-2.5 text-base font-heading">
                    <SlidersHorizontal className="h-4 w-4 text-[#E11D48]" /> Пункты договора
                  </span>
                </AccordionTrigger>
                <AccordionContent>
                  <p className="text-xs text-muted-foreground mb-4">
                    Текст добавляется в соответствующий раздел договора. Пустые пункты не меняют
                    оригинальный документ — форма остаётся 1:1.
                  </p>
                  <div className="space-y-4">
                    {SECTIONS.map((s) => (
                      <div key={s.key} className="space-y-1.5">
                        <Label className="text-sm text-white">{s.title}</Label>
                        <Textarea
                          className="rounded-sm bg-[#0A0A0C] border-white/10 focus:border-[#E11D48] min-h-[70px]"
                          placeholder="Добавить пункт в этот раздел…"
                          value={fields[s.key] || ""}
                          onChange={(e) => update(s.key, e.target.value)}
                          data-testid={`section-${s.key}`}
                        />
                      </div>
                    ))}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </div>

          {/* Right: live preview */}
          <div className="flex flex-col bg-[#050506] max-h-[62vh] lg:max-h-[74vh]">
            <div className="flex items-center justify-between gap-3 px-4 py-2.5 border-b border-white/10">
              <div className="flex items-center gap-2 text-sm">
                <Eye className="h-4 w-4 text-[#E11D48]" />
                <span className="font-medium">Живой просмотр</span>
                {previewing && <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />}
              </div>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer">
                  <Switch checked={autoRefresh} onCheckedChange={setAutoRefresh} data-testid="auto-refresh-switch" />
                  Авто
                </label>
                <Button
                  variant="ghost" size="sm" className="rounded-sm h-8"
                  onClick={() => refreshPreview(fields)}
                  disabled={previewing}
                  data-testid="refresh-preview-btn"
                >
                  <RefreshCw className={`h-4 w-4 ${previewing ? "animate-spin" : ""}`} /> Обновить
                </Button>
                {previewUrl && (
                  <Button
                    variant="ghost" size="sm" className="rounded-sm h-8"
                    onClick={() => window.open(previewUrl, "_blank")}
                    title="Открыть в новой вкладке"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
            <div className="flex-1 min-h-[320px] relative">
              {previewUrl ? (
                <object data={previewUrl} type="application/pdf" className="w-full h-full" data-testid="editor-preview">
                  <iframe title="preview" src={previewUrl} className="w-full h-full border-0" />
                </object>
              ) : (
                <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
                  <Loader2 className="h-6 w-6 animate-spin mr-2" /> Готовим предпросмотр…
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2 px-6 py-3 border-t border-white/10 bg-card">
          <Button
            variant="outline"
            className="rounded-sm border-white/15"
            onClick={() => handleSave("draft", "draft")}
            disabled={!!busy}
            data-testid="save-draft-btn"
          >
            {busy === "draft" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileClock className="h-4 w-4" />}
            Сохранить черновик
          </Button>
          <div className="flex flex-wrap gap-2 justify-end">
            <Button
              variant="outline" className="rounded-sm border-white/15"
              onClick={handlePrint} disabled={!!busy}
              data-testid="editor-print-btn"
            >
              {busy === "print" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Printer className="h-4 w-4" />}
              Печать
            </Button>
            <Button
              variant="outline" className="rounded-sm border-white/15"
              onClick={() => handleDownload("pdf")} disabled={!!busy}
              data-testid="editor-download-pdf-btn"
            >
              {busy === "pdf" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileType className="h-4 w-4" />}
              PDF
            </Button>
            <Button
              variant="outline" className="rounded-sm border-white/15"
              onClick={() => handleDownload("docx")} disabled={!!busy}
              data-testid="editor-download-docx-btn"
            >
              {busy === "docx" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
              Word
            </Button>
            <Button
              className="rounded-sm bg-[#E11D48] hover:bg-[#BE123C] text-white active:scale-95 transition-transform"
              onClick={() => handleSave("final", "final")}
              disabled={!!busy}
              data-testid="save-final-btn"
            >
              {busy === "final" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Сохранить в историю
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
