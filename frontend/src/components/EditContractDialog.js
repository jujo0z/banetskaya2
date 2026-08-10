import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { FIELDS, SECTIONS } from "@/lib/fields";
import { saveContract, downloadSavedContract, previewPdfUrl, api } from "@/lib/apiClient";
import { toast } from "sonner";
import { FileText, FileType, Printer, Save, Loader2, Eye, SlidersHorizontal, FormInput } from "lucide-react";
import DocumentPreviewDialog from "@/components/DocumentPreviewDialog";

export default function EditContractDialog({ open, student, onClose, onSaved }) {
  const [fields, setFields] = useState(student || {});
  const [savedId, setSavedId] = useState(null);
  const [busy, setBusy] = useState("");
  const [previewUrl, setPreviewUrl] = useState(null);

  const [lastStudent, setLastStudent] = useState(student);
  if (student !== lastStudent) {
    setLastStudent(student);
    setFields(student || {});
    setSavedId(null);
  }

  const update = (key, value) => setFields((prev) => ({ ...prev, [key]: value }));

  async function ensureSaved() {
    if (savedId) return savedId;
    const created = await saveContract(fields);
    setSavedId(created.id);
    onSaved && onSaved();
    return created.id;
  }

  async function handleSave() {
    try {
      setBusy("save");
      await ensureSaved();
      toast.success("Договор сохранён в историю");
    } catch (e) {
      toast.error("Не удалось сохранить договор");
    } finally {
      setBusy("");
    }
  }

  async function handlePreview() {
    try {
      setBusy("preview");
      const url = await previewPdfUrl(fields);
      setPreviewUrl(url);
    } catch (e) {
      toast.error("Не удалось открыть просмотр");
    } finally {
      setBusy("");
    }
  }

  async function handleDownload(format) {
    try {
      setBusy(format);
      const id = await ensureSaved();
      await downloadSavedContract(id, format, `Договор.${format}`);
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
      const id = await ensureSaved();
      const res = await api.get(`/contracts/${id}/download`, {
        params: { format: "pdf" },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(res.data);
      const w = window.open(url);
      if (w) w.onload = () => w.print();
      toast.success("Документ открыт для печати");
    } catch (e) {
      toast.error("Не удалось открыть для печати");
    } finally {
      setBusy("");
    }
  }

  return (
    <>
      <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
        <DialogContent
          className="max-w-4xl max-h-[92vh] overflow-y-auto rounded-none bg-card border-white/10"
          data-testid="edit-contract-dialog"
        >
          <DialogHeader>
            <DialogTitle className="font-heading text-3xl tracking-tight">
              Правка и модерация договора
            </DialogTitle>
            <DialogDescription>
              Отредактируйте поля из Excel и при необходимости добавьте собственные пункты в разделы договора.
            </DialogDescription>
          </DialogHeader>

          <Tabs defaultValue="fields" className="mt-2">
            <TabsList className="rounded-none bg-transparent border-b border-white/10 p-0 h-auto w-full justify-start gap-6">
              <TabsTrigger
                value="fields"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#E11D48] data-[state=active]:bg-transparent data-[state=active]:text-white px-1 pb-3 pt-2"
                data-testid="tab-fields"
              >
                <FormInput className="h-4 w-4 mr-2" /> Данные
              </TabsTrigger>
              <TabsTrigger
                value="moderation"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-[#E11D48] data-[state=active]:bg-transparent data-[state=active]:text-white px-1 pb-3 pt-2"
                data-testid="tab-moderation"
              >
                <SlidersHorizontal className="h-4 w-4 mr-2" /> Модерация пунктов
              </TabsTrigger>
            </TabsList>

            <TabsContent value="fields" className="mt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {FIELDS.map((f) => (
                  <div key={f.key} className="space-y-1.5">
                    <Label className="text-xs uppercase tracking-[0.1em] text-muted-foreground">
                      {f.label}
                    </Label>
                    <Input
                      className="rounded-sm bg-[#0A0A0C] border-white/10 focus:border-[#E11D48]"
                      value={fields[f.key] || ""}
                      onChange={(e) => update(f.key, e.target.value)}
                      data-testid={`field-${f.key}`}
                    />
                  </div>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="moderation" className="mt-6">
              <p className="text-sm text-muted-foreground mb-5">
                Текст, добавленный в раздел, вставляется в договор в соответствующем месте. Пустые
                разделы не меняют оригинальный документ.
              </p>
              <div className="space-y-5">
                {SECTIONS.map((s) => (
                  <div key={s.key} className="space-y-1.5">
                    <Label className="font-heading text-lg text-white">{s.title}</Label>
                    <Textarea
                      className="rounded-sm bg-[#0A0A0C] border-white/10 focus:border-[#E11D48] min-h-[80px]"
                      placeholder="Добавить пункт в этот раздел…"
                      value={fields[s.key] || ""}
                      onChange={(e) => update(s.key, e.target.value)}
                      data-testid={`section-${s.key}`}
                    />
                  </div>
                ))}
              </div>
            </TabsContent>
          </Tabs>

          <DialogFooter className="flex-col sm:flex-row gap-2 sm:justify-between border-t border-white/10 pt-4 mt-4">
            <Button
              variant="outline"
              className="rounded-sm border-white/15"
              onClick={handleSave}
              disabled={!!busy}
              data-testid="save-history-btn"
            >
              {busy === "save" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              В историю
            </Button>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                className="rounded-sm border-white/15"
                onClick={handlePreview}
                disabled={!!busy}
                data-testid="preview-btn"
              >
                {busy === "preview" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Eye className="h-4 w-4" />}
                Просмотр
              </Button>
              <Button
                variant="outline"
                className="rounded-sm border-white/15"
                onClick={handlePrint}
                disabled={!!busy}
                data-testid="print-btn"
              >
                {busy === "print" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Printer className="h-4 w-4" />}
                Печать
              </Button>
              <Button
                variant="outline"
                className="rounded-sm border-white/15"
                onClick={() => handleDownload("pdf")}
                disabled={!!busy}
                data-testid="download-pdf-btn"
              >
                {busy === "pdf" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileType className="h-4 w-4" />}
                PDF
              </Button>
              <Button
                className="rounded-sm bg-[#E11D48] hover:bg-[#BE123C] text-white active:scale-95 transition-transform"
                onClick={() => handleDownload("docx")}
                disabled={!!busy}
                data-testid="download-docx-btn"
              >
                {busy === "docx" ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
                Скачать Word
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <DocumentPreviewDialog
        open={!!previewUrl}
        url={previewUrl}
        title="Просмотр договора"
        onClose={() => {
          if (previewUrl) window.URL.revokeObjectURL(previewUrl);
          setPreviewUrl(null);
        }}
      />
    </>
  );
}
